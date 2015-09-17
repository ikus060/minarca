package com.patrikdufresne.rdiffweb.core;

import java.util.Date;

/**
 * Represent information related to a single repository.
 * 
 * @author Patrik Dufresne
 * 
 */
public class RepositoryInfo {

    private Date lastBackup;

    private String name;

    public Date getLastBackup() {
        return lastBackup;
    }

    public String getName() {
        return name;
    }

    public void setLastBackup(Date lastBackup) {
        this.lastBackup = lastBackup;
    }

    public void setName(String name) {
        this.name = name;
    }

}
