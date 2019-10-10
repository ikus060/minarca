package com.patrikdufresne.minarca.core;

/**
 * Define the schedule.
 * 
 * @author Patrik Dufresne
 * 
 */
public enum Schedule {
    DAILY(24), HOURLY(1), MONTHLY(720), WEEKLY(168);

    public int delta;

    private Schedule(int delta) {
        this.delta = delta;
    }

}