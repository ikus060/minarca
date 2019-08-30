/*
 * Copyright (C) 2019, Patrik Dufresne Service Logiciel inc. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.core;

import static com.patrikdufresne.minarca.core.Localized._;

import java.io.File;
import java.io.IOException;
import java.io.Writer;
import java.text.DateFormat;
import java.util.Date;
import java.util.Properties;

import org.apache.commons.configuration.ConfigurationException;
import org.apache.commons.configuration.PropertiesConfiguration;
import org.apache.commons.configuration.reloading.FileChangedReloadingStrategy;
import org.apache.commons.lang3.StringUtils;
import org.apache.commons.lang3.Validate;
import org.apache.commons.logging.impl.NoOpLog;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.patrikdufresne.minarca.core.internal.Compat;

public class Status {

    private static final transient Logger LOGGER = LoggerFactory.getLogger(Status.class);

    /**
     * Property name.
     */
    private static final String PROPERTY_LAST_DATE = "lastdate";

    /**
     * Property name.
     */
    private static final String PROPERTY_LAST_RESULT = "lastresult";

    /**
     * Property name.
     */
    private static final String PROPERTY_LAST_SUCCESS = "lastsuccess";

    /**
     * Load the status from default status file.
     * 
     * @return
     */
    public static Status fromFile() {
        LOGGER.debug("reading properties from [{}]", Compat.STATUS_FILE);
        PropertiesConfiguration status;
        try {
            status = load(Compat.STATUS_FILE);
        } catch (ConfigurationException e1) {
            LOGGER.warn("can't load properties {}", Compat.STATUS_FILE);
            return new Status(LastResult.UNKNOWN, null, null);
        }
        // Last date
        Date lastDate;
        try {
            Long value = status.getLong(PROPERTY_LAST_DATE);
            lastDate = new Date(value.longValue());
        } catch (Exception e) {
            lastDate = null;
        }
        // Last success
        Date lastSuccess;
        try {
            Long value = status.getLong(PROPERTY_LAST_SUCCESS);
            lastSuccess = new Date(value.longValue());
        } catch (Exception e) {
            lastSuccess = null;
        }
        // Last Results
        LastResult lastResult;
        try {
            String value = status.getString(PROPERTY_LAST_RESULT);
            if (value == null) {
                lastResult = LastResult.HAS_NOT_RUN;
            } else {
                lastResult = LastResult.valueOf(value);
                if (LastResult.RUNNING.equals(lastResult)) {
                    Date now = new Date();
                    if (lastDate != null && lastDate.getTime() < now.getTime() - (API.RUNNING_DELAY * 2)) {
                        lastResult = LastResult.STALE;
                    }
                }
            }
        } catch (Exception e) {
            lastResult = LastResult.UNKNOWN;
        }
        return new Status(lastResult, lastDate, lastSuccess);
    }

    /**
     * Load properties.
     * 
     * @throws ConfigurationException
     * 
     * @throws APIException
     */
    private static PropertiesConfiguration load(File file) throws ConfigurationException {
        PropertiesConfiguration properties = new PropertiesConfiguration();
        properties = new PropertiesConfiguration(file);
        properties.setLogger(new NoOpLog());
        properties.setAutoSave(false);
        properties.setReloadingStrategy(new FileChangedReloadingStrategy());
        return properties;
    }

    /**
     * Used to persist the configuration.
     * 
     * @throws IOException
     */
    private static void save(File file, Properties properties) throws IOException {
        LOGGER.trace("writing status to [{}]", file);
        Writer writer = Compat.openFileWriter(file, Compat.CHARSET_DEFAULT);
        properties.store(writer, API.getCopyrightText() + "\r\nMinarca backup state.\r\n" + "Please do not change this configuration file manually.");
        writer.close();
    }

    /**
     * Set the last status.
     * 
     * @param state
     *            the right state.
     * @param date
     *            the date
     * @throws APIException
     */
    protected static void setLastStatus(LastResult state) throws APIException {
        Validate.notNull(state);
        Properties newStatus = new Properties();
        String now = Long.toString(new Date().getTime());
        newStatus.setProperty(PROPERTY_LAST_RESULT, state.toString());
        newStatus.setProperty(PROPERTY_LAST_DATE, now);
        if (LastResult.SUCCESS.equals(state)) {
            newStatus.setProperty(PROPERTY_LAST_SUCCESS, now);
        } else {
            Date d = fromFile().getLastSuccess();
            if (d != null) {
                newStatus.setProperty(PROPERTY_LAST_SUCCESS, Long.toString(d.getTime()));
            }
        }
        try {
            save(Compat.STATUS_FILE, newStatus);
        } catch (IOException e) {
            throw new APIException(_("fail to save config"), e);
        }
    }

    private Date lastDate;

    private LastResult lastResult;

    private Date lastSuccess;

    public Status(LastResult lastResult, Date lastDate, Date lastSuccess) {
        Validate.notNull(this.lastResult = lastResult);
        this.lastDate = lastDate;
        this.lastSuccess = lastSuccess;
    }

    /**
     * Retrieve the last result.
     * 
     * @return the last result.
     */
    public LastResult getLastResult() {
        return lastResult;

    }

    /**
     * Return the last backup date. (success or failure)
     * 
     * @return
     */
    public Date getLastResultDate() {
        return lastDate;
    }

    /**
     * Return the last successful backup date.
     * 
     * @return Date of last success or null.
     */
    public Date getLastSuccess() {
        return lastSuccess;
    }

    /**
     * Return a string to represent the current status.
     * 
     * @return
     */
    public String getLocalized() {
        LastResult lastResult = getLastResult();
        Date lastDate = getLastResultDate();
        String date = lastDate != null ? DateFormat.getDateTimeInstance().format(lastDate) : StringUtils.EMPTY;
        switch (lastResult) {
        case RUNNING:
            return _("Running");
        case SUCCESS:
            return date + " " + _("Successful");
        case FAILURE:
            return date + " " + _("Failed");
        case HAS_NOT_RUN:
            return _("Never run");
        case STALE:
            return date + " " + _("Stale");
        case INTERRUPT:
            return date + " " + _("Interrupt");
        default:
            return date + " " + _("Unknown");
        }
    }

}
