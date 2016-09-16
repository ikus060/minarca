/*
 * Copyright (C) 2015, Patrik Dufresne Service Logiciel inc. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.core.internal;

import com.patrikdufresne.minarca.core.APIException;
import com.patrikdufresne.minarca.core.Schedule;
import com.patrikdufresne.minarca.core.APIException.ScheduleNotFoundException;

public class SchedulerLinux extends Scheduler {

    @Override
    public void create(Schedule schedule) {
        // TODO Auto-generated method stub
    }

    @Override
    public boolean delete() {
        // TODO Auto-generated method stub
        return false;
    }

    @Override
    public boolean exists() throws APIException {
        // TODO Auto-generated method stub
        return false;
    }

    @Override
    public Schedule getSchedule() throws APIException, ScheduleNotFoundException {
        // TODO Auto-generated method stub
        return null;
    }

    @Override
    public void run() throws APIException {
        // TODO Auto-generated method stub

    }

    @Override
    public void terminate() throws APIException {
        // TODO Auto-generated method stub

    }

}
