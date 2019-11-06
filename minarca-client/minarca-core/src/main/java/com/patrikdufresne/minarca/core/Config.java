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
import java.security.NoSuchAlgorithmException;
import java.security.interfaces.RSAPublicKey;
import java.security.spec.InvalidKeySpecException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Properties;

import org.apache.commons.configuration.ConfigurationException;
import org.apache.commons.configuration.PropertiesConfiguration;
import org.apache.commons.configuration.reloading.FileChangedReloadingStrategy;
import org.apache.commons.lang3.Validate;
import org.apache.commons.logging.impl.NoOpLog;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.patrikdufresne.minarca.core.internal.Compat;
import com.patrikdufresne.minarca.core.internal.Keygen;

/**
 * Class responsible to fetch and return configuration for the API.
 * 
 * @author Patrik Dufresne
 * 
 */
public class Config {

    /**
     * Filename used for configuration file. Notice, this is also read by batch file.
     */
    private static final String FILENAME_CONF = "minarca.properties";

    /**
     * Includes filename.
     */
    private static final String FILENAME_GLOB_PATTERNS = "patterns";;

    private static final transient Logger LOGGER = LoggerFactory.getLogger(Config.class);

    /**
     * Property name.
     */
    private static final String PROPERTY_REMOTEHOST = "remotehost";

    /**
     * Property name.
     */
    private static final String PROPERTY_REMOTEURL = "remoteurl";

    /**
     * Property name.
     */
    private static final String PROPERTY_REPOSITORY_NAME = "repositoryname";

    /**
     * Property name.
     */
    private static final String PROPERTY_SCHEDULE = "schedule";

    /**
     * Property name.
     */
    private static final String PROPERTY_USERNAME = "username";

    /**
     * Property name.
     */
    private static final String PROPERTY_CONFIGURED = "configured";

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
     * Reference to the configuration file.
     */
    private File confFile;

    /**
     * Reference to file patterns.
     */
    private File globPatternsFile;

    private List<GlobPattern> patterns = Collections.emptyList();

    /**
     * Reference to the configuration.
     */
    private PropertiesConfiguration properties;

    public Config() {
        this.confFile = new File(Compat.CONFIG_HOME, FILENAME_CONF); // $NON-NLS-1$
        this.globPatternsFile = new File(Compat.CONFIG_HOME, FILENAME_GLOB_PATTERNS); // $NON-NLS-1$
        // Load the configuration
        load();
    }

    /**
     * Return the remote URL to Minarca server.
     * 
     * @return
     */
    public String getRemoteUrl() {
        return this.properties.getString(PROPERTY_REMOTEURL);
    }

    /**
     * Return the include patterns used for the backup.
     * 
     * @return the list of pattern.
     */
    public List<GlobPattern> getGlobPatterns() {
        return this.patterns;
    }

    public File getGlobPatternsFile() {
        return globPatternsFile;
    }

    /**
     * Generate a finger print from id_rsa file.
     * 
     * @return the finger print.
     * @throws APIException
     */
    public String getIdentityFingerPrint() {
        File file = getPublicKeyFile();
        if (!file.isFile() || !file.canRead()) {
            LOGGER.warn("public key [{}] is not accessible", file);
            return "";
        }
        try {
            RSAPublicKey publicKey = Keygen.fromPublicIdRsa(file);
            return Keygen.getFingerPrint(publicKey);
        } catch (InvalidKeySpecException | NoSuchAlgorithmException | IOException e) {
            LOGGER.warn("cannot read key [{}] ", file, e);
        }
        return "";
    }

    /**
     * Return the location of the known_hosts file to be used for OpenSSH.
     * 
     * @return
     */
    public File getKnownHosts() {
        return new File(Compat.CONFIG_HOME, "known_hosts");
    }

    /**
     * Return the location of the identify file.
     * 
     * @return the identity file.
     */
    protected File getPrivateKeyFile() {
        return new File(Compat.CONFIG_HOME, "id_rsa");
    }

    /**
     * Return the location of the public key.
     * 
     * @return
     */
    protected File getPublicKeyFile() {
        return new File(Compat.CONFIG_HOME, "id_rsa.pub");
    }

    /**
     * Return the remote host to be used for SSH communication.
     * <p>
     * Current implementation return the same SSH server. In future, this implementation might changed to request the
     * web server for a specific URL.
     * 
     * @return
     */
    public String getRemotehost() {
        return this.properties.getString(PROPERTY_REMOTEHOST);
    }

    /**
     * Friendly named used to represent the repository being backup.
     * 
     * @return the repository name.
     */
    public String getRepositoryName() {
        return this.properties.getString(PROPERTY_REPOSITORY_NAME);
    }

    /**
     * Get the scheduling preferences.
     * 
     * @return The schedule
     * 
     */
    public Schedule getSchedule() {
        try {
            return Schedule.valueOf(this.properties.getString(PROPERTY_SCHEDULE));
        } catch (Exception e) {
            return Schedule.DAILY;
        }
    }

    /**
     * Get the username used for the backup (username used to authentication with SSH server).
     * 
     * @return
     */
    public String getUsername() {
        return this.properties.getString(PROPERTY_USERNAME);
    }

    /**
     * True if minarca was configured.
     */
    public boolean getConfigured() {
        return Boolean.valueOf(this.properties.getString(PROPERTY_CONFIGURED));
    }

    public void load() {
        LOGGER.debug("reading properties from [{}]", this.confFile);
        try {
            this.properties = load(this.confFile);
        } catch (ConfigurationException e1) {
            LOGGER.warn("can't load properties {}", this.confFile);
        }
        LOGGER.debug("reading glob patterns from [{}]", this.globPatternsFile);
        try {
            this.patterns = GlobPattern.readPatterns(this.globPatternsFile);
        } catch (IOException e) {
            LOGGER.warn("can't glob patterns from {}", this.confFile);
        }
    }

    /**
     * Save all the configuration.
     * 
     * @throws APIException
     */
    public void save() throws APIException {
        try {
            this.properties.save();
        } catch (ConfigurationException e) {
            throw new APIException(_("fail to save config"), e);
        }
        try {
            LOGGER.debug("writing patterns to [{}]", globPatternsFile);
            GlobPattern.writePatterns(globPatternsFile, patterns);
        } catch (IOException e) {
            throw new APIException(_("fail to save config"), e);
        }
    }

    /**
     * Sets a new pattern list.
     * 
     * @param patterns
     * @throws APIException
     */
    public void setGlobPatterns(List<GlobPattern> patterns, boolean save) throws APIException {
        Validate.notNull(patterns);
        this.patterns = new ArrayList<>(patterns);
        if (save) save();
    }

    /**
     * Sets remote host.
     * 
     * @param value
     * @throws APIException
     */
    public void setRemotehost(String value, boolean save) throws APIException {
        this.properties.setProperty(PROPERTY_REMOTEHOST, value);
        if (save) save();
    }

    /**
     * Sets if minarca is configured.
     * 
     * @param value
     * @param save
     * @throws APIException
     */
    public void setConfigured(boolean value, boolean save) throws APIException {
        this.properties.setProperty(PROPERTY_CONFIGURED, value);
        if (save) save();
    }

    /**
     * Sets the remove url.
     * 
     * @param value
     * @param save
     * @throws APIException
     */
    public void setRemoteUrl(String value, boolean save) throws APIException {
        this.properties.setProperty(PROPERTY_REMOTEURL, value);
        if (save) save();
    }

    /**
     * Sets the repository name.
     * 
     * @param value
     * @throws APIException
     */
    public void setRepositoryName(String value, boolean save) throws APIException {
        this.properties.setProperty(PROPERTY_REPOSITORY_NAME, value);
        if (save) save();
    }

    /**
     * Define the scheduling preferences.
     * 
     * @param schedule
     *            the new schedule.
     */
    public void setSchedule(Schedule schedule, boolean save) throws APIException {
        Validate.notNull(schedule);
        this.properties.setProperty(PROPERTY_SCHEDULE, schedule.toString());
        if (save) save();
    }

    /**
     * Sets the username.
     * 
     * @param value
     * @throws APIException
     */
    public void setUsername(String value, boolean save) throws APIException {
        this.properties.setProperty(PROPERTY_USERNAME, value);
        if (save) save();
    }

}
