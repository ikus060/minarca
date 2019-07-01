/*
 * Copyright (C) 2018, Patrik Dufresne Service Logiciel inc. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.core.internal;

import static com.patrikdufresne.minarca.Localized._;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Scanner;
import java.util.regex.Pattern;

import org.apache.commons.lang3.StringUtils;
import org.apache.commons.lang3.SystemUtils;
import org.apache.commons.lang3.Validate;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.patrikdufresne.minarca.core.APIException;

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
    private static class TaskInfoWin {

        private static final String[] WINDOWS_7_INDEXES = new String[] {
                "HOSTNAME",
                "TASKNAME",
                "NEXT_RUN_TIME",
                "STATUS",
                "",
                "LAST_RUN_TIME",
                "LAST_RESULT",
                "AUTHOR",
                "TASK_TO_RUN",
                "",
                "COMMENT",
                "STATE",
                "",
                "",
                "RUN_AS",
                "",
                "",
                "",
                "SCHEDULE_TYPE",
                "START_TIME" };

        private static final String[] WINDOWS_XP_INDEXES = new String[] {
                "HOSTNAME",
                "TASKNAME",
                "NEXT_RUN_TIME",
                "STATUS",
                "LAST_RUN_TIME",
                "LAST_RESULT",
                "AUTHOR",
                "",
                "TASK_TO_RUN",
                "",
                "COMMENT",
                "STATE",
                "SCHEDULE_TYPE",
                "START_TIME" };

        private final List<String> data;
        private final List<String> INDEXES;
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
         * Return the task name.
         * 
         * @return
         */
        String getTaskname() {
            return get(TASKNAME);
        }

        @Override
        public String toString() {
            return "SchTaskEntry [taskname=" + getTaskname() + "]";
        }

    }

    /**
     * Pattern used to detect error.
     */
    private static final Pattern ERROR_PATTERN = Pattern.compile("(ERROR|ERREUR)");

    private static final transient Logger LOGGER = LoggerFactory.getLogger(SchedulerWindows.class);

    /**
     * Windows task name.
     */
    private static final String TASK_NAME = "Minarca backup";

    private static final String QUOTE = "\"";

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
    public synchronized void create() throws APIException {
        LOGGER.debug("creating schedule task [{}]", TASK_NAME);

        // Delete the tasks (if exists). The /F option doesn't exists in WinXP.
        if (SystemUtils.IS_OS_WINDOWS_XP || SystemUtils.IS_OS_WINDOWS_2003) {
            delete();
        }
        List<String> args = new ArrayList<String>();
        args.add("/Create");

        // Define task name
        args.add("/TN");
        args.add(TASK_NAME);

        // Define command to execute
        args.add("/TR");
        args.add(QUOTE + getExeLocation() + QUOTE + " --backup");

        if (!SystemUtils.IS_OS_WINDOWS_XP && !SystemUtils.IS_OS_WINDOWS_2003) {
            // Add Force object to replace existing task.
            args.add("/F");
        }
        if (SystemUtils.IS_OS_WINDOWS_XP || SystemUtils.IS_OS_WINDOWS_2003) {
            // Run task as Admin
            args.add("/RU");
            args.add("SYSTEM");
        }

        // Define schedule
        args.add("/SC");
        args.add("HOURLY");

        // Execute the command.
        String data = execute(args);

        // FIXME looking at command output is not the best since it change according to user language.
        if (ERROR_PATTERN.matcher(data).find()) {
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
    public synchronized boolean delete() throws APIException {
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
            p.waitFor();
            return sh.getOutput();
        } catch (IOException e) {
            throw new APIException("fail to create subprocess", e);
        } catch (InterruptedException e) {
            // Swallow. Should no happen
            LOGGER.warn("process interrupted", e);
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
    @Override
    public synchronized boolean exists() {
        try {
            TaskInfoWin task = query(TASK_NAME);
            if (task == null) {
                return false;
            }
            List<String> expectedCommands = new ArrayList<>();
            // For WinXP
            // The current command won't contains any quote or single quote. It's a shame.
            expectedCommands.add(getExeLocation() + " --backup");
            expectedCommands.add(getExeLocation() + "  --backup");

            // For Win 7 & +
            // Replace the " by \" to match our command line
            expectedCommands.add(QUOTE + getExeLocation() + QUOTE + " --backup");
            expectedCommands.add(QUOTE + getExeLocation() + QUOTE + "  --backup");

            if (!expectedCommands.contains(task.getCommand())) {
                LOGGER.warn("command [{}] doesn't matched expected command {}", task.getCommand(), expectedCommands);
                return false;
            }
            return true;
        } catch (

        Exception e) {
            LOGGER.warn("can't detect the task", e);
            return false;
        }
    }

    /**
     * Return the location of the executable.
     * 
     * @return
     */
    protected File getExeLocation() {
        return MinarcaExecutable.getMinarcaLocation();
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
            if (t.getTaskname() != null && t.getTaskname().toLowerCase().endsWith(taskname.toLowerCase())) {
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
    private TaskInfoWin query(String taskname) throws APIException {
        Validate.notNull(taskname);
        return internalQueryCsv(taskname);
    }

}
