/*
 * Copyright (C) 2018, Patrik Dufresne Service Logiciel inc. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.core;

import static com.patrikdufresne.minarca.Localized._;

import java.io.File;
import java.io.IOException;
import java.security.KeyPair;
import java.security.interfaces.RSAPrivateKey;
import java.security.interfaces.RSAPublicKey;
import java.util.Arrays;
import java.util.Date;
import java.util.List;
import java.util.Objects;

import org.apache.commons.io.FileUtils;
import org.apache.commons.lang3.StringUtils;
import org.apache.commons.lang3.SystemUtils;
import org.apache.commons.lang3.Validate;
import org.apache.http.client.HttpResponseException;
import org.apache.http.conn.HttpHostConnectException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.patrikdufresne.minarca.core.APIException.AuthenticationException;
import com.patrikdufresne.minarca.core.APIException.ConnectivityException;
import com.patrikdufresne.minarca.core.APIException.ExchangeSshKeyException;
import com.patrikdufresne.minarca.core.APIException.GenerateKeyException;
import com.patrikdufresne.minarca.core.APIException.InitialBackupFailedException;
import com.patrikdufresne.minarca.core.APIException.InitialBackupHasNotRunException;
import com.patrikdufresne.minarca.core.APIException.InitialBackupRunningException;
import com.patrikdufresne.minarca.core.APIException.LinkComputerException;
import com.patrikdufresne.minarca.core.APIException.MissConfiguredException;
import com.patrikdufresne.minarca.core.APIException.RepositoryNameAlreadyInUseException;
import com.patrikdufresne.minarca.core.APIException.ScheduleNotFoundException;
import com.patrikdufresne.minarca.core.APIException.UnsupportedOS;
import com.patrikdufresne.minarca.core.internal.Compat;
import com.patrikdufresne.minarca.core.internal.Keygen;
import com.patrikdufresne.minarca.core.internal.MinarcaExecutable;
import com.patrikdufresne.minarca.core.internal.RdiffBackup;
import com.patrikdufresne.minarca.core.internal.Scheduler;
import com.patrikdufresne.minarca.core.internal.SchedulerLinux;
import com.patrikdufresne.minarca.core.internal.SchedulerWindows;
import com.patrikdufresne.minarca.core.model.CurrentUser;
import com.patrikdufresne.minarca.core.model.MinarcaInfo;

/**
 * This class is the main entry point to do everything related to minarca.
 * 
 * @author Patrik Dufresne
 * 
 */
public class API {

    /**
     * Singleton instance of API
     */
    private static API instance;

    /**
     * The logger.
     */
    private static final transient Logger LOGGER = LoggerFactory.getLogger(API.class);

    /**
     * Delay 5 sec.
     */
    protected static final int RUNNING_DELAY = 5000;

    /**
     * Used to check if the current running environment is valid. Check supported OS, check permissions, etc. May also
     * check running application version.
     * 
     * @throws APIException
     */
    public static void checkEnv() throws APIException {
        // Check OS and VM version.
        LOGGER.info("{} {} {}", SystemUtils.OS_NAME, SystemUtils.OS_VERSION, SystemUtils.OS_ARCH);
        LOGGER.info("{} (build {}, {})", SystemUtils.JAVA_VM_INFO, SystemUtils.JAVA_VM_VERSION, SystemUtils.JAVA_VM_INFO);
        if (!(SystemUtils.IS_OS_WINDOWS || SystemUtils.IS_OS_LINUX)) {
            LOGGER.warn("unsupported OS");
            throw new UnsupportedOS();
        }
    }

    public static Config config() {
        return instance().config;
    }

    /**
     * Return the single instance of API.
     * 
     * @return
     */
    public static API instance() {
        if (instance == null) {
            instance = new API();
        }
        return instance;
    }

    protected Config config;

    /**
     * Default constructor.
     */
    private API() {
        this.config = new Config();
    }

    /**
     * Used to start a backup.
     * 
     * @param background
     *            True to asynchronously start the backup process. This operation usually used the system scheduler to
     *            run the backup task in background.
     * @param force
     *            True to force the execution of
     * 
     * @throws APIException
     * @throws InterruptedException
     */
    public void backup(boolean background, boolean force) throws APIException, InterruptedException {
        // To run in background, we start a new minarca process.
        if (background) {
            MinarcaExecutable minarca = new MinarcaExecutable();
            minarca.backup(force);
            return;
        }

        // Check if properly configure (from our point of view).
        try {
            checkConfig();
        } catch (APIException e) {
            // Show error message (usually localized).
            LOGGER.info("invalid config", e);
            config.setLastStatus(LastResult.FAILURE);
            throw e;
        }

        // If not forced, we need to check if it's time to run a backup.
        if (!force && !isBackupTime(config)) {
            LOGGER.info("not time to backup");
            return;
        }

        Thread t = new Thread() {
            @Override
            public void run() {
                try {
                    while (true) {
                        try {
                            config.setLastStatus(LastResult.RUNNING);
                        } catch (APIException e) {
                            // Nothing to do.
                        }
                        sleep(RUNNING_DELAY);
                    }
                } catch (InterruptedException e) {
                    // Nothing to do.
                }
            }
        };
        t.setDaemon(true);
        t.start();

        // Get the config value.
        String remotehost = config.getRemotehost();
        String repositoryName = config.getRepositoryName();

        // Get reference to the identity file to be used by ssh or plink.
        File knownHosts = config.getKnownHosts();
        File identityFile = config.getPrivateKeyFile();

        // Create a new instance of rdiff backup to test and run the backup.
        RdiffBackup rdiffbackup = new RdiffBackup(remotehost, knownHosts, identityFile);

        // Read patterns
        List<GlobPattern> patterns = config.getGlobPatterns();
        if (patterns.isEmpty()) {
            t.interrupt();
            LOGGER.info("fail to read patterns");
            config.setLastStatus(LastResult.FAILURE);
            throw new APIException(_("fail to read selective backup settings"));
        }
        // By default ignore minarca log files
        String logFolder = System.getProperty("log.folder");
        if (StringUtils.isNotEmpty(logFolder)) {
            patterns.add(new GlobPattern(false, new File(logFolder, "minarca-log*.txt")));
        }
        try {
            // Check the remote server.
            rdiffbackup.testServer(repositoryName);
            // Run backup.
            rdiffbackup.backup(patterns, repositoryName);
            t.interrupt();
            config.setLastStatus(LastResult.SUCCESS);
            LOGGER.info("backup SUCCESS");
        } catch (InterruptedException e) {
            t.interrupt();
            config.setLastStatus(LastResult.INTERRUPT);
            LOGGER.info("backup INTERUPT", e);
            throw new APIException(_("Backup interrupted"), e);
        } catch (Exception e) {
            t.interrupt();
            config.setLastStatus(LastResult.FAILURE);
            LOGGER.info("backup FAILED", e);
            throw new APIException(_("Backup failed"), e);
        }

    }

    /**
     * Used to check if the configuration is OK. Called as a sanity check to make sure "minarca" is properly configured.
     * If not, it throw an exception.
     * 
     * @return
     */
    public void checkConfig() throws APIException {
        // Basic sanity check to make sure it's configured. If not, display the
        // setup dialog.
        if (StringUtils.isBlank(config.getRepositoryName())) {
            throw new MissConfiguredException(_("Missing repository name"));
        }
        if (StringUtils.isBlank(config.getUsername())) {
            throw new MissConfiguredException(_("Missing username"));
        }
        if (StringUtils.isBlank(config.getRemotehost())) {
            throw new MissConfiguredException(_("Missing remote host"));
        }
        if (StringUtils.isBlank(config.getRemoteUrl())) {
            throw new MissConfiguredException(_("Missing remote server URL"));
        }
        // Check if SSH keys exists.
        File identityFile = config.getPrivateKeyFile();
        if (!identityFile.isFile() || !identityFile.canRead()) {
            throw new MissConfiguredException(_("identity file doesn't exists or is not accessible"));
        }

        // Check if known_hosts exists.
        File knownHostsFile = config.getKnownHosts();
        if (!knownHostsFile.isFile() || !knownHostsFile.canRead()) {
            throw new MissConfiguredException(_("remote server identity (known_hosts) file doesn't exists or is not accessible"));
        }

        // Don't verify patterns. See pdsl/minarca/#105
        // Instead, check if the files exists.
        if (!config.getGlobPatternsFile().isFile()) {
            throw new MissConfiguredException(_("selective backup settings are missing"));
        }

    }

    /**
     * Establish connection to minarca web service.
     * 
     * @return a new client instance
     * 
     * @throws APIException
     *             if the connection can't be established.
     */
    public Client connect(String baseurl, String username, String password) throws APIException {
        // Create a new client instance.
        // Add http if not provided.
        if (!(baseurl.startsWith("http://") || baseurl.startsWith("https://"))) {
            baseurl = "http://" + baseurl;
        }
        Client client = new Client(baseurl, username, password);

        // Check connectivity
        try {
            client.check();
        } catch (HttpResponseException e) {
            // Raised when status code >=300
            if (e.getStatusCode() == 401) {
                throw new AuthenticationException(e);
            }
            throw new APIException(_("Unknown server error."), e);
        } catch (HttpHostConnectException e) {
            // Raised on connection failure
            throw new ConnectivityException(e);
        } catch (Exception e) {
            throw new APIException(_("Authentication failed for unknown reason."), e);
        }
        return client;
    }

    protected Scheduler getScheduler() {
        if (SystemUtils.IS_OS_WINDOWS) {
            return new SchedulerWindows();
        } else if (SystemUtils.IS_OS_LINUX) {
            return new SchedulerLinux();
        }
        throw new UnsupportedOperationException(SystemUtils.OS_NAME + " not supported");
    }

    /**
     * Check if it's time to backup according to user preferences.
     * 
     * @return True if we may backup.
     */
    private boolean isBackupTime(Config config) {
        Date last = config.getLastSuccess();
        if (last == null) {
            return true;
        }
        Schedule schedule = config.getSchedule();
        long delta = schedule.delta * 60l * 60l * 1000;
        delta = delta * 98 / 100;
        return delta < new Date().getTime() - last.getTime();
    }

    /**
     * Register a new computer.
     * <p>
     * A successful link of this computer will generate a new configuration file.
     * <p>
     * This implementation will generate public and private keys for putty. The public key will be sent to minarca. The
     * computer name is added to the comments.
     * 
     * 
     * @param repositoryName
     *            friendly name to represent this computer.
     * @param client
     *            reference to web client
     * @param force
     *            True to force usage of existing computer name.
     * @throws GenerateKeyException
     *             if the keys can't be created.
     * @throws ExchangeSshKeyException
     *             if the SSH Keys can't be sent to the server.
     * @throws InterruptedException
     * @throws IOException
     *             communication error with minarca website.
     * @throws IllegalAccessException
     *             if the repository name is not valid.
     * @throws RepositoryNameAlreadyInUseException
     *             is the repository name already exists on the server and `force` is false.
     * @throws IllegalArgumentException
     *             if the arguments are invalid.
     */
    public void link(final String repositoryName, Client client, boolean force) throws APIException, InterruptedException, IOException {
        Validate.notNull(client);
        Validate.notEmpty(repositoryName, _("repository name cannot be empty"));
        Validate.isTrue(repositoryName.matches("[a-zA-Z][a-zA-Z0-9\\-\\.]*"), _("repository must only contains letters, numbers, dash (-) and dot (.)"));

        /*
         * Check if repository name is already in uses.
         */
        CurrentUser userInfo = client.getCurrentUserInfo();
        boolean exists = !userInfo.findRepos(repositoryName).isEmpty();
        if (!force && exists) {
            throw new RepositoryNameAlreadyInUseException(repositoryName);
        }

        /*
         * Generate the keys
         */
        LOGGER.debug("generating public and private key for {}", repositoryName);
        File idrsaFile = config.getPublicKeyFile();
        File identityFile = config.getPrivateKeyFile();
        String rsadata = null;
        try {
            // Generate a key pair.
            KeyPair pair = Keygen.generateRSA();
            // Generate a simple id_rsa.pub file.
            Keygen.toPublicIdRsa((RSAPublicKey) pair.getPublic(), repositoryName, idrsaFile);
            // Generate a private key file.
            Keygen.toPrivatePEM((RSAPrivateKey) pair.getPrivate(), identityFile);
            // Read RSA pub key.
            rsadata = FileUtils.readFileToString(idrsaFile);
        } catch (Exception e) {
            throw new GenerateKeyException(e);
        }

        // Send SSH key to minarca server using web service.
        try {
            client.addSSHKey(repositoryName, rsadata);
        } catch (IOException e) {
            throw new ExchangeSshKeyException(e);
        }

        // Query info from WebServer
        MinarcaInfo minarcaInfo = client.getMinarcaInfo();

        // Replace known_hosts file
        String knownHosts = minarcaInfo.identity;
        FileUtils.write(config.getKnownHosts(), knownHosts);

        // Generate configuration file.
        String username = userInfo.username;
        String remoteHost = minarcaInfo.remotehost;
        LOGGER.debug("saving configuration [{}][{}][{}]", repositoryName, username, remoteHost);
        config.setUsername(username, false);
        config.setRepositoryName(repositoryName, false);
        config.setRemotehost(remoteHost, false);
        config.setRemoteUrl(client.getRemoteUrl(), false);

        // Create default schedule
        config.setSchedule(Schedule.DAILY, false);

        // If the backup doesn't exists on the remote server, start an empty initial backup.
        if (exists) {
            LOGGER.debug("repository already exists");
            config.setConfigured(true, true);
            config.save();
            return;
        }

        // Empty the include
        List<GlobPattern> previousPatterns = config.getGlobPatterns();
        config.setGlobPatterns(Arrays.asList(new GlobPattern(false, Compat.getRootsPath()[0] + "**")), false);

        // Reset Last result
        Date lastResultDate = config.getLastResultDate();

        // Run backup
        config.save();
        backup(true, true);

        // Refresh list of repositories (10 min)
        int attempt = Integer.getInteger("minarca.link.timeoutsec", 600 /* 5*60*100 */) * 1000 / RUNNING_DELAY;
        do {
            Thread.sleep(RUNNING_DELAY);
            attempt--;
            try {
                client.updateRepositories();
                // Check if repo exists in minarca.
                exists = !client.getCurrentUserInfo().findRepos(repositoryName).isEmpty();
                if (exists) {
                    LOGGER.debug("repository {} found", repositoryName);
                    break;
                }
            } catch (IOException e) {
                LOGGER.warn("io error", e);
            }
            // Check if backup task is completed.
            if (!Objects.equals(lastResultDate, config.getLastResultDate()) && !LastResult.RUNNING.equals(config.getLastResult())) {
                LOGGER.debug("schedule task not running");
                attempt = Math.min(attempt, 1);
            }
        } while (attempt > 0);

        // Restore glob patterns
        config.setGlobPatterns(previousPatterns, false);

        // Check if repository exists.
        if (!exists) {

            // Unset properties
            config.setUsername(null, false);
            config.setRepositoryName(null, false);
            config.setRemotehost(null, false);
            config.save();

            // Check if the backup schedule ran.
            switch (config.getLastResult()) {
            case RUNNING:
                throw new InitialBackupRunningException(null);
            case FAILURE:
            case STALE:
                throw new InitialBackupFailedException(null);
            case HAS_NOT_RUN:
                throw new InitialBackupHasNotRunException(null);
            case SUCCESS:
            case UNKNOWN:
            default:
                throw new LinkComputerException(null);
            }
        }
        // Mark minarca as configured.
        config.setConfigured(true, true);

        // Setup the scheduler
        Scheduler scheduler = getScheduler();
        scheduler.create();

        // Set encoding
        try {
            LOGGER.debug("updating repository [{}] encoding [{}]", repositoryName, Compat.CHARSET_DEFAULT.toString());
            client.setRepoEncoding(repositoryName, Compat.CHARSET_DEFAULT.toString());
        } catch (Exception e) {
            LOGGER.warn("fail to configure repository encoding", e);
        }

    }

    /**
     * Used to stop a running backup task.
     * 
     * @throws APIException
     * @throws ScheduleNotFoundException
     */
    public void stopBackup() throws ScheduleNotFoundException, APIException {
        MinarcaExecutable minarca = new MinarcaExecutable();
        minarca.stop();
    }

    /**
     * Check if this computer is properly link to minarca.net.
     * 
     * @throws APIException
     * @throws InterruptedException
     */
    public void testServer() throws APIException, InterruptedException {

        // Get the config value.
        String remotehost = config.getRemotehost();
        String repositoryName = config.getRepositoryName();

        // Get reference to the identity file to be used by ssh.
        File knownHosts = config.getKnownHosts();
        File identityFile = config.getPrivateKeyFile();

        // Create a new instance of rdiff backup to test and run the backup.
        RdiffBackup rdiffbackup = new RdiffBackup(remotehost, knownHosts, identityFile);

        // Check the remote server.
        rdiffbackup.testServer(repositoryName);

    }

    /**
     * Used to unlink this computer.
     * 
     * @throws APIException
     */
    public void unlink() throws APIException {
        // To unlink, delete the configuration and schedule task.
        config.setRepositoryName(null, false);
        config.setUsername(null, false);
        config.setRemotehost(null, false);
        config.save();

        // TODO Remove RSA keys

        // TODO Remove RSA key from client too.

        // Delete task
        Scheduler scheduler = getScheduler();
        scheduler.delete();
    }
}
