/*
 * Copyright (C) 2015, Patrik Dufresne Service Logiciel inc. All rights reserved.
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

    private static class SchTaskEntry {

        private static final int TASK_TO_RUN = 8;

        private static final int TASKNAME = 1;

        List<String> data;

        private SchTaskEntry(List<String> data) {
            Validate.notNull(this.data = data);
        }

        private String get(int index) {
            return this.data.get(index);
        }

        public String getCommand() {
            return get(TASK_TO_RUN);
        }

        public String getTaskname() {
            return get(TASKNAME);
        }

        @Override
        public String toString() {
            return "SchTaskEntry [taskname=" + getTaskname() + "]";
        }

    }

    private static final transient Logger LOGGER = LoggerFactory.getLogger(SchedulerWindows.class);

    /**
     * Property used to define the location of minarca.bat file.
     */
    private static final String PROPERTY_MINARCA_EXE_LOCATION = "minarca.exe.location";

    /**
     * Executable launch to start backup.
     */
    private static final String MINARCA;
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
     * Windows task name.
     */
    private static final String TASK_NAME = "minarca backup";

    public SchedulerWindows() {

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
            SchTaskEntry task = query(TASK_NAME);
            if (task == null) {
                return false;
            }
            String curCommand;
            String expectedCommand;
            if (SystemUtils.IS_OS_WINDOWS_XP) {
                // For WinXP
                // The current command won't contains any quote or single quote. It's a shame.
                curCommand = task.getCommand().trim();
                curCommand = curCommand.replace("  --backup", " --backup");
                expectedCommand = getCommand().replace("\\\"", "");
            } else {
                // For Win 7
                // Replace the " by \" to match our command line
                curCommand = task.getCommand().trim();
                expectedCommand = getCommand().replace("\\\"", "\"");
            }
            if (!curCommand.equals(expectedCommand)) {
                LOGGER.warn("command [{}] doesn't matched expected command [{}]", curCommand, expectedCommand);
                return false;
            }
            return true;
        } catch (APIException e) {
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
            throw new APIException(_("{0} is missing ", MINARCA));
        }
        StringBuilder buf = new StringBuilder();
        buf.append("\\\"");
        buf.append(file);
        buf.append("\\\" --backup");
        return buf.toString();
    }

    private List<SchTaskEntry> internalQuery(String taskname) throws APIException {
        String data;
        if (taskname != null && !SystemUtils.IS_OS_WINDOWS_XP && !SystemUtils.IS_OS_WINDOWS_2003) {
            // Query a specific taskname.
            data = execute("/Query", "/FO", "CSV", "/V", "/TN", taskname);
        } else {
            data = execute("/Query", "/FO", "CSV", "/V");
        }
        // Read the first line
        Scanner scanner = new Scanner(data);
        if (!scanner.hasNextLine()) {
            scanner.close();
            return Collections.emptyList();
        }
        List<SchTaskEntry> list = new ArrayList<SchedulerWindows.SchTaskEntry>();
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
            SchTaskEntry task = new SchTaskEntry(map);
            list.add(task);
        }
        scanner.close();
        return list;
    }

    /**
     * Query the given taskname.
     * 
     * @param taskname
     * @throws APIException
     */
    private SchTaskEntry query(String taskname) throws APIException {
        // Find a matching taskname.
        for (SchTaskEntry t : internalQuery(taskname)) {
            if (t.getTaskname() != null && t.getTaskname().endsWith(taskname)) {
                return t;
            }
        }
        return null;
    }

    @Override
    public void run() throws APIException {
        // TODO Auto-generated method stub

    }

    protected File getExeLocation() {
        return Compat.searchFile(MINARCA, System.getProperty(PROPERTY_MINARCA_EXE_LOCATION), "./bin/", ".");
    }

}
