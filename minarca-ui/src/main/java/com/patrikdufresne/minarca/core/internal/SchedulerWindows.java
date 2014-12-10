/*
 * Copyright (c) 2014, Patrik Dufresne Service Logiciel. All rights reserved.
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
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Scanner;

import org.apache.commons.lang.StringUtils;
import org.apache.commons.lang.Validate;
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

        private static final String TASK_TO_RUN = "Task To Run";

        private static final String TASKNAME = "TaskName";

        // ["HostName", "TaskName", "Next Run Time", "Status", "Logon Mode",
        // "Last Run Time", "Last Result", "Author", "Task To Run", "Start In",
        // "Comment", "Scheduled Task State", "Idle Time", "Power Management",
        // "Run As User", "Delete Task If Not Rescheduled",
        // "Stop Task If Runs X Hours and X Mins", "Schedule", "Schedule Type",
        // "Start Time", "Start Date", "End Date", "Days", "Months",
        // "Repeat: Every", "Repeat: Until: Time", "Repeat: Until: Duration",
        // "Repeat: Stop If Still Running"]

        Map<String, String> data;

        private SchTaskEntry(Map<String, String> data) {
            Validate.notNull(this.data = data);
        }

        public String get(String key) {
            return this.data.get(key);
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
     * Script being called by the scheduler to start a bat file hidden.
     */
    private static final String MINARCA_LAUNCH_VBS = "launch.vbs";

    /**
     * Property used to define the location of minarca.bat file.
     */
    private static final String PROPERTY_MINARCA_BATCH_LOCATION = "minarca.bat.location";

    /**
     * Windows task name.
     */
    private static final String TASK_NAME = "minarca backup";

    /**
     * Return the command line to be executed to run a backup.
     * 
     * @return
     * @throws APIException
     */
    public String getCommand() throws APIException {
        return "'" + search(MINARCA_LAUNCH_VBS) + "'";
    }

    /**
     * Search for a binary file.
     * 
     * @return
     * @throws APIException
     */
    private static File search(String filename) throws APIException {
        // Search minarca.bat file
        List<String> locations = new ArrayList<String>();
        String value = System.getProperty(PROPERTY_MINARCA_BATCH_LOCATION);
        if (value != null) {
            locations.add(value);
        }
        locations.add("./bin/");
        locations.add(".");
        for (String location : locations) {
            File file = new File(location, filename);
            if (file.isFile() && file.canRead()) {
                try {
                    return file.getCanonicalFile();
                } catch (IOException e) {
                    return file.getAbsoluteFile();
                }
            }
        }
        throw new APIException(_("{0} is missing ", filename));
    }

    /**
     * Remove leading and ending quote.
     * 
     * @param string
     * @return
     */
    private static String trimQuote(String string) {
        return string.replaceAll("^\"", "").replaceAll("\"$", "");
    }

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
        String data = execute("/Create", "/SC", "HOURLY", "/TN", TASK_NAME, "/TR", getCommand(), "/F");
        if (!data.contains("SUCCESS")) {
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
    private String execute(List<String> args) throws APIException {
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
            String curCommand = task.getCommand().replace("\"", "'");
            return task != null && getCommand().equals(curCommand);
        } catch (APIException e) {
            LOGGER.warn("can't detect the task", e);
            return false;
        }
    }

    private List<SchTaskEntry> internalQuery(String taskname) throws APIException {
        String data;
        if (taskname != null) {
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
        String[] columns = line.split(",");
        while (scanner.hasNextLine()) {
            Map<String, String> map = new LinkedHashMap<String, String>();
            line = scanner.nextLine();
            String[] values = line.split(",");
            if (Arrays.equals(columns, values)) {
                continue;
            }
            for (int i = 0; i < columns.length && i < values.length; i++) {
                map.put(trimQuote(columns[i]), trimQuote(values[i]));
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
}
