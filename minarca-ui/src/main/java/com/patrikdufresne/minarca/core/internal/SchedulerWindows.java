/*
 * Copyright (C) 2015, Patrik Dufresne Service Logiciel inc. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.core.internal;

import static com.patrikdufresne.minarca.Localized._;

import java.io.File;
import java.io.IOException;
import java.text.DateFormat;
import java.text.ParseException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Date;
import java.util.List;
import java.util.Scanner;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.apache.commons.lang3.StringUtils;
import org.apache.commons.lang3.SystemUtils;
import org.apache.commons.lang3.Validate;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.patrikdufresne.minarca.core.APIException;
import com.patrikdufresne.minarca.core.APIException.TaskNotFoundException;

/**
 * Wrapper around "schtasks" command line.
 * 
 * @author Patrik Dufresne
 * 
 */
public class SchedulerWindows extends Scheduler {

    /**
     * Instance of this class represent a task in Windows scheduler (used for CSV entry).
     * 
     * @author Patrik Dufresne
     * 
     */
    private static class TaskInfoWin implements TaskInfo {

        private static final String[] WINDOWS_XP_INDEXES = new String[] {
                "HOSTNAME",
                "TASKNAME",
                "NEXT_RUN_TIME",
                "STATUS",
                "LAST_RUN_TIME",
                "LAST_RESULT",
                "AUTHOR",
                "",
                "TASK_TO_RUN" };

        private static final String[] WINDOWS_7_INDEXES = new String[] {
                "HOSTNAME",
                "TASKNAME",
                "NEXT_RUN_TIME",
                "STATUS",
                "",
                "LAST_RUN_TIME",
                "LAST_RESULT",
                "AUTHOR",
                "TASK_TO_RUN" };

        /**
         * Heuristic to parse date string.
         * 
         * @param value
         *            a date in string format.
         * 
         * @return a Date object or null
         */
        private static Date parseDate(String value) {
            // Build list of DateFormat
            List<DateFormat> dateformats = Arrays.asList(
                    DateFormat.getDateTimeInstance(DateFormat.SHORT, DateFormat.SHORT),
                    DateFormat.getDateTimeInstance(DateFormat.SHORT, DateFormat.MEDIUM),
                    DateFormat.getDateTimeInstance(DateFormat.SHORT, DateFormat.LONG),
                    DateFormat.getDateTimeInstance(DateFormat.SHORT, DateFormat.FULL),
                    DateFormat.getDateTimeInstance(DateFormat.MEDIUM, DateFormat.MEDIUM),
                    DateFormat.getDateTimeInstance(DateFormat.MEDIUM, DateFormat.LONG),
                    DateFormat.getDateTimeInstance(DateFormat.MEDIUM, DateFormat.FULL),
                    DateFormat.getDateTimeInstance(DateFormat.LONG, DateFormat.LONG),
                    DateFormat.getDateTimeInstance(DateFormat.LONG, DateFormat.FULL),
                    DateFormat.getDateTimeInstance(DateFormat.FULL, DateFormat.FULL),
                    DateFormat.getDateInstance());
            // May need to reverse values.
            List<String> values = new ArrayList<String>();
            values.add(value);
            String parts[] = value.split(", ");
            if (parts.length == 2) {
                values.add(parts[1] + " " + parts[0]);
            }
            for (String v : values) {
                for (DateFormat df : dateformats) {
                    try {
                        return df.parse(v);
                    } catch (ParseException e) {
                        // Swallow
                    }
                }
            }
            LOGGER.debug("fail to parse date [{}]", value);
            return null;
        }

        private final List<String> data;
        private final List<String> INDEXES;
        private final int LAST_RESULT;
        private final int LAST_RUN_TIME;
        private final int STATUS;
        private final int TASK_TO_RUN;
        private final int TASKNAME;

        /**
         * Create a new task entry.
         * 
         * @param data
         *            raw data.
         */
        private TaskInfoWin(List<String> data) {
            Validate.notNull(data);
            this.data = Collections.unmodifiableList(new ArrayList<String>(data));
            if (data.size() >= 28 /* || SystemUtils.IS_OS_WINDOWS_10 */) {
                // Windows 10
                INDEXES = Arrays.asList(WINDOWS_7_INDEXES);
            } else {
                INDEXES = Arrays.asList(WINDOWS_XP_INDEXES);
            }
            LAST_RESULT = INDEXES.indexOf("LAST_RESULT");
            LAST_RUN_TIME = INDEXES.indexOf("LAST_RUN_TIME");
            STATUS = INDEXES.indexOf("STATUS");
            TASK_TO_RUN = INDEXES.indexOf("TASK_TO_RUN");
            TASKNAME = INDEXES.indexOf("TASKNAME");
        }

        private String get(int index) {
            return this.data.get(index);
        }

        /**
         * Return the command being run by the task. It doesn't return it in a compatible way. Extra processing may be
         * required.
         * 
         * @return
         */
        String getCommand() {
            return get(TASK_TO_RUN);
        }

        /**
         * Return the last known return code.
         * 
         * @return the return code.
         */
        @Override
        public Integer getLastResult() {
            String value = get(LAST_RESULT);
            try {
                return Integer.parseInt(value);
            } catch (NumberFormatException e) {
                return null;
            }
        }

        /**
         * Return the last run time.
         * 
         * @return the last run time date.
         */
        @Override
        public Date getLastRun() {
            String value = get(LAST_RUN_TIME);
            return parseDate(value);
        }

        /**
         * Return the state of the task. If it's running or not. etc.
         * 
         * @return
         */
        String getStatus() {
            return get(STATUS);
        }

        /**
         * Return the task name.
         * 
         * @return
         */
        String getTaskname() {
            return get(TASKNAME);
        }

        @Override
        public Boolean isRunning() {
            // Get the status and check if it run.
            LOGGER.debug("task status [{}]", getStatus());
            Matcher m = PATTERN_TASK_RUNNING.matcher(getStatus());
            return m.find();
        }

        @Override
        public String toString() {
            return "SchTaskEntry [taskname=" + getTaskname() + "]";
        }

    }

    private static final transient Logger LOGGER = LoggerFactory.getLogger(SchedulerWindows.class);

    /**
     * Executable launch to start backup.
     */
    private static final String MINARCA;

    /**
     * Regex pattern used to check if the task is running.
     */
    private static final Pattern PATTERN_TASK_RUNNING = Pattern.compile("(En cours d'exécution|Running)");

    /**
     * Property used to define the location of minarca.bat file.
     */
    private static final String PROPERTY_MINARCA_EXE_LOCATION = "minarca.exe.location";
    /**
     * Windows task name.
     */
    private static final String TASK_NAME = "minarca backup";

    static {
        if (SystemUtils.IS_OS_WINDOWS) {
            if (SystemUtils.JAVA_VM_NAME.contains("64-Bit")) {
                MINARCA = "minarca64.exe";
            } else {
                MINARCA = "minarca.exe";
            }
        } else {
            MINARCA = "minarca.sh";
        }
    }

    /**
     * Create a new schedule tasks
     * 
     * <pre>
     * SCHTASKS /Create [/S system [/U username [/P password]]]
     *     [/RU username [/RP password]] /SC schedule [/MO modifier] [/D day]
     *     [/I idletime] /TN taskname /TR taskrun [/ST starttime] [/M months]
     *     [/SD startdate] [/ED enddate]
     * </pre>
     * 
     * @throws APIException
     * 
     * @see http ://www.windowsnetworking.com/kbase/WindowsTips/WindowsXP/AdminTips
     *      /Utilities/XPschtaskscommandlineutilityreplacesAT.exe.html
     */
    public void create() throws APIException {
        LOGGER.debug("creating schedule task [{}]", TASK_NAME);
        String data;
        if (SystemUtils.IS_OS_WINDOWS_XP || SystemUtils.IS_OS_WINDOWS_2003) {
            // Delete the tasks (if exists). The /F option doesn't exists in WinXP.
            delete();
            // Create the task.
            data = execute("/Create", "/SC", "HOURLY", "/TN", TASK_NAME, "/TR", getCommand(), "/RU", "SYSTEM");
        } else {
            // Otherwise
            if (Compat.IS_ADMIN) {
                // If running in admin mode, run minarca backup as SYSTEM user.
                data = execute("/Create", "/SC", "HOURLY", "/TN", TASK_NAME, "/TR", getCommand(), "/RU", "SYSTEM", "/F");
            } else {
                // Otherwise, run minarca backup as current user.
                data = execute("/Create", "/SC", "HOURLY", "/TN", TASK_NAME, "/TR", getCommand(), "/F");
            }
        }
        // FIXME looking at command output is not the best since it change according to user language.
        if (data.matches("(ERROR|ERREUR)")) {
            throw new APIException("fail to schedule task");
        }
    }

    /**
     * Delete the task named <code>taskname</code>.
     * 
     * @param taskname
     *            the task to be deleted.
     * @throws APIException
     */
    public boolean delete() throws APIException {
        LOGGER.debug("deleting schedule task [{}]", TASK_NAME);
        String data = execute("/Delete", "/F", "/TN", TASK_NAME);
        return data.contains("SUCCESS");
    }

    /**
     * Used to execute the command.
     * 
     * @throws APIException
     */
    String execute(List<String> args) throws APIException {
        List<String> command = new ArrayList<String>();
        command.add("schtasks.exe");
        if (args != null) {
            command.addAll(args);
        }
        LOGGER.debug("executing {}", StringUtils.join(command, " "));
        try {
            Process p = new ProcessBuilder().command(command).redirectErrorStream(true).start();
            StreamHandler sh = new StreamHandler(p);
            sh.start();
            // TODO Check return code.
            p.waitFor();
            return sh.getOutput();
        } catch (IOException e) {
            throw new APIException("fail to create subprocess", e);
        } catch (InterruptedException e) {
            // Swallow. Should no happen
            LOGGER.warn("process interupted", e);
            Thread.currentThread().interrupt();
        }
        return null;
    }

    /**
     * Used to execute the command.
     * 
     * @param args
     * @return
     * @throws APIException
     */
    private String execute(String... args) throws APIException {
        return execute(Arrays.asList(args));
    }

    /**
     * Check if a task with the given name exists.
     * 
     * @param taskName
     *            the task name.
     * @return True if exists.
     */
    public boolean exists() {
        try {
            TaskInfo task = query(TASK_NAME);
            if (task == null) {
                return false;
            }
            String curCommand;
            String expectedCommand;
            if (task instanceof TaskInfoWin) {
                if (SystemUtils.IS_OS_WINDOWS_XP || SystemUtils.IS_OS_WINDOWS_2003) {
                    // For WinXP
                    // The current command won't contains any quote or single quote. It's a shame.
                    curCommand = ((TaskInfoWin) task).getCommand().trim();
                    curCommand = curCommand.replace("  --backup", " --backup");
                    expectedCommand = getCommand().replace("\\\"", "");
                } else {
                    // For Win 7 & +
                    // Replace the " by \" to match our command line
                    curCommand = ((TaskInfoWin) task).getCommand().trim();
                    expectedCommand = getCommand().replace("\\\"", "\"");
                }
            } else {
                LOGGER.warn("unsupported TaskInfo [{}]", task);
                return false;
            }
            if (!curCommand.equals(expectedCommand)) {
                LOGGER.warn("command [{}] doesn't matched expected command [{}]", curCommand, expectedCommand);
                return false;
            }
            return true;
        } catch (Exception e) {
            LOGGER.warn("can't detect the task", e);
            return false;
        }
    }

    /**
     * Return the command line to be executed to run a backup.
     * 
     * @return
     * @throws APIException
     */
    private String getCommand() throws APIException {
        File file = getExeLocation();
        if (file == null) {
            throw new APIException(_("{0} is missing", MINARCA));
        }
        StringBuilder buf = new StringBuilder();
        buf.append("\\\"");
        buf.append(file);
        buf.append("\\\" --backup");
        return buf.toString();
    }

    protected File getExeLocation() {
        return Compat.searchFile(MINARCA, System.getProperty(PROPERTY_MINARCA_EXE_LOCATION), "./bin/", ".");
    }

    /**
     * Get information about the task.
     */
    @Override
    public TaskInfo info() throws TaskNotFoundException, APIException {
        LOGGER.info("check task info");
        // Get reference to our task
        TaskInfo task = query(TASK_NAME);
        if (task == null) {
            throw new TaskNotFoundException();
        }
        return task;
    }

    /**
     * To support Windows XP and Windows 2003. Read data as CSV.
     * 
     * @param taskname
     *            the task name.
     * @return the task information.
     * @throws APIException
     */
    private TaskInfoWin internalQueryCsv(String taskname) throws APIException {
        // Execute the query command.
        String data;
        if (SystemUtils.IS_OS_WINDOWS_2003 || SystemUtils.IS_OS_WINDOWS_XP) {
            data = execute("/Query", "/FO", "CSV", "/V");
        } else {
            data = execute("/Query", "/FO", "CSV", "/V", "/TN", taskname);
        }
        // Read the first line
        Scanner scanner = new Scanner(data);
        if (!scanner.hasNextLine()) {
            scanner.close();
            return null;
        }
        List<TaskInfoWin> list = new ArrayList<TaskInfoWin>();
        String line = scanner.nextLine();
        String[] columns = line.split("\",\"");
        while (scanner.hasNextLine()) {
            List<String> map = new ArrayList<String>();
            line = scanner.nextLine();
            // Remove leading and ending double-quote then split the line.
            String[] values = line.replaceFirst("^\"", "").replaceFirst("\"$", "").split("\",\"");
            if (Arrays.equals(columns, values)) {
                continue;
            }
            for (int i = 0; i < columns.length && i < values.length; i++) {
                map.add((values[i]));
            }
            list.add(new TaskInfoWin(map));
        }
        scanner.close();
        for (TaskInfoWin t : list) {
            if (t.getTaskname() != null && t.getTaskname().endsWith(taskname)) {
                return t;
            }
        }
        return null;
    }

    /**
     * Query the given taskname.
     * 
     * @param taskname
     * @throws APIException
     */
    private TaskInfo query(String taskname) throws APIException {
        Validate.notNull(taskname);
        return internalQueryCsv(taskname);
    }

    /**
     * Start the task.
     */
    @Override
    public void run() throws APIException {
        LOGGER.info("starting the task");
        execute("/Run", "/TN", TASK_NAME);
    }

    /**
     * End the task.
     */
    @Override
    public void terminate() throws APIException {
        LOGGER.info("terminating the task");
        execute("/End", "/TN", TASK_NAME);
    }

}
