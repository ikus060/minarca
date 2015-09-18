package com.patrikdufresne.minarca.core.internal;

import java.util.Date;

/**
 * Create a task info.
 * 
 * @author Patrik Dufresne
 */
public interface SchedulerTask {

    /**
     * Define the schedule.
     * 
     * @author Patrik Dufresne
     * 
     */
    public enum Schedule {
        DAILY, HOURLY, MONTHLY, UNKNOWN, WEEKLY
    }

    /**
     * The last result of the task.
     * 
     * @return
     */
    public Integer getLastResult();

    /**
     * The last known running date.
     * 
     * @return
     */
    public Date getLastRun();

    /**
     * Return the current task schedule.
     * 
     * @return
     */
    public SchedulerTask.Schedule getSchedule();

    /**
     * True if the task is running.
     * 
     * @return
     */
    public Boolean isRunning();

}