/*
 * Copyright (C) 2018, Patrik Dufresne Service Logiciel inc. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.core.internal;

import java.io.File;
import java.io.IOException;
import java.util.Calendar;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.patrikdufresne.minarca.core.APIException;
import com.patrikdufresne.minarca.core.APIException.MinarcaMissingException;
import com.patrikdufresne.minarca.core.internal.Crontab.CrontabEntry;

public class SchedulerLinux extends Scheduler {

    private static final transient Logger LOGGER = LoggerFactory.getLogger(SchedulerLinux.class);

    @Override
    public void create() throws APIException {
        LOGGER.debug("creating crontab entry");

        // Create a new date to pick hour and minute.
        Calendar c = Calendar.getInstance();
        c.add(Calendar.MINUTE, -1);
        String minute = Integer.toString(c.get(Calendar.MINUTE));

        try {
            // Delete cronjob if exists.
            delete();
            // Create a new entry and add it.
            Crontab.addEntry(new CrontabEntry(minute, "*", "*", "*", "*", getExeLocation() + " --backup"));
        } catch (IOException e) {
            throw new APIException(e);
        }
    }

    @Override
    public boolean delete() throws APIException {
        LOGGER.debug("deleting schedule task");
        try {
            // Find a cron tab entry.
            CrontabEntry entry = find();
            if (entry != null) {
                // Delete the entry if exists.
                Crontab.removeEntry(entry);
                return true;
            }
        } catch (IOException e) {
            throw new APIException(e);
        }
        return false;
    }

    @Override
    public boolean exists() {
        try {
            return find() != null;
        } catch (Exception e) {
            return false;
        }
    }

    /**
     * Create a matching cron tab entry int the cron tab.
     * 
     * @return a cron tab entry or null.
     * @throws IOException
     * @throws APIException
     */
    protected CrontabEntry find() throws IOException, MinarcaMissingException {
        // Create the crontab.
        Crontab crontab = getCrontab();
        // Identify the entry to be deleted;
        String command = getExeLocation() + " --backup";
        for (CrontabEntry e : crontab.getEntries()) {
            if (command.equals(e.getCommand())) {
                return e;
            }
        }
        LOGGER.trace("command line [{}] not found in crontab entries [{}]", command, crontab.getAllEntries().size());
        return null;
    }

    /**
     * Return current user crontab.
     * 
     * @return
     * @throws IOException
     */
    protected Crontab getCrontab() throws IOException {
        return Crontab.readAll();
    }

    /**
     * Return the location of the executable.
     * 
     * @return
     */
    protected File getExeLocation() {
        return MinarcaExecutable.getMinarcaLocation();
    }

}
