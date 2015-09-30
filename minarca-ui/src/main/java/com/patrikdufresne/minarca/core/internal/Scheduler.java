/*
 * Copyright (C) 2015, Patrik Dufresne Service Logiciel inc. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.core.internal;

import org.apache.commons.lang3.SystemUtils;

import com.patrikdufresne.minarca.core.APIException;
import com.patrikdufresne.minarca.core.APIException.TaskNotFoundException;

/**
 * Interface used to represent a scheduler.
 * <p>
 * Class implementing this interface represent the scheduling service used by the current operating system. This
 * interface is indented to represent a subset of the feature provided by the scheduler.
 * 
 * @author Patrik Dufresne
 * 
 */
public abstract class Scheduler {

    public static Scheduler singleton;

    /**
     * Return the scheduling service for this operating system.
     * 
     * @return the scheduler service.
     * @throws UnsupportedOperationException
     *             if OS is not supported
     */
    public static Scheduler getInstance() {
        if (singleton != null) {
            return singleton;
        }
        if (SystemUtils.IS_OS_WINDOWS) {
            return singleton = new SchedulerWindows();
        } else if (SystemUtils.IS_OS_LINUX) {
            return singleton = new SchedulerLinux();
        }
        throw new UnsupportedOperationException(SystemUtils.OS_NAME + " not supported");
    }

    /**
     * Create a new task in the scheduler
     * 
     * @param taskname
     * @param command
     */
    public abstract void create(SchedulerTask.Schedule schedule) throws APIException;

    /**
     * Delete the task
     * 
     * @param taskname
     */
    public abstract boolean delete() throws APIException;

    /**
     * Check if the schedule task exists.
     * 
     * @return True if the task exists.
     * @throws APIException
     */
    public abstract boolean exists() throws APIException;

    /**
     * Check if the task exists.
     * 
     * @param taskname
     * @return
     */
    public abstract SchedulerTask info() throws APIException, TaskNotFoundException;

    /**
     * Run the task.
     * 
     * @throws APIException
     */
    public abstract void run() throws APIException, TaskNotFoundException;

    /**
     * Terminate the task. Has no effect if the task is not running.
     * 
     * @throws APIException
     */
    public abstract void terminate() throws APIException, TaskNotFoundException;
}
