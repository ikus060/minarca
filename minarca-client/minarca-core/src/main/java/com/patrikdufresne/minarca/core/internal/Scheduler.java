/*
 * Copyright (C) 2019, Patrik Dufresne Service Logiciel inc. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.core.internal;

import org.apache.commons.lang3.SystemUtils;

import com.patrikdufresne.minarca.core.APIException;

/**
 * Interface used to represent a scheduler.
 * <p>
 * Class implementing this interface represent the scheduling service used by the current operating system. This
 * interface is indented to represent a subset of the feature provided by the scheduler. The main purpose is to register
 * a task hourly and Minarca will decide to backup or not according to user preferences.
 * 
 * @author Patrik Dufresne
 * 
 */
public abstract class Scheduler {

    /**
     * Create a new task in the scheduler
     * 
     * @param taskname
     * @param command
     */
    public abstract void create() throws APIException;

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
    public abstract boolean exists();

}
