package com.patrikdufresne.minarca.core.internal;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import org.apache.commons.io.FileUtils;
import org.apache.commons.lang3.StringUtils;
import org.apache.commons.lang3.SystemUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.patrikdufresne.minarca.core.APIException;

/**
 * This utility class provide different method to ease access to Windows OS ressources: scheduler, registry, execute
 * process, etc.
 * 
 * @author ikus060
 * 
 */
public class OSUtils {

    /**
     * Location where to store configuration for minarca.
     */
    public static String ADMIN_CONFIG_PATH;

    /**
     * True if the user is admin.
     */
    public static final boolean IS_ADMIN;

    /**
     * Logger used.
     */
    private static final transient Logger LOGGER;

    /**
     * Path to system profile for Windows OS.
     * <p>
     * Under non-windows OS, this constant is null.
     */
    public static final String WINDOWS_SYSTEMPROFILE_PATH;

    static {
        // Use a static block to declare constant value in the right order.
        LOGGER = LoggerFactory.getLogger(OSUtils.class);
        WINDOWS_SYSTEMPROFILE_PATH = getWindowsSystemProfilePath();
        ADMIN_CONFIG_PATH = getAdminConfigPath();
        IS_ADMIN = getIsAdmin();
    }

    /**
     * Return the location of the configuration for minarca when running with admin right.
     * 
     * @return
     */
    private static String getAdminConfigPath() {
        if (SystemUtils.IS_OS_WINDOWS) { //$NON-NLS-1$
            if (SystemUtils.IS_OS_WINDOWS_XP || SystemUtils.IS_OS_WINDOWS_2003) {
                return OSUtils.WINDOWS_SYSTEMPROFILE_PATH + "/Application Data/minarca";
            }
            return OSUtils.WINDOWS_SYSTEMPROFILE_PATH + "/AppData/Local/minarca";
        } else if (SystemUtils.IS_OS_LINUX) {
            return "/etc/minarca";
        }
        throw new UnsupportedOperationException(SystemUtils.OS_NAME + " not supported");
    }

    /**
     * Return true if the user is admin.
     * <p>
     * This implementation make multiple assumption about administrator right. It checks if user can access the "SYSTEM"
     * registry hive. Can read-write to SYSTEM user profile.
     * 
     * @return
     */
    private static boolean getIsAdmin() {
        if (SystemUtils.IS_OS_WINDOWS) {
            // Query the SYSTEM registry hive.
            try {
                reg("query", "HKU\\S-1-5-18");
            } catch (APIException e) {
                return false;
            }
            // Check if the minarca directory can be created.
            try {
                File file = new File(ADMIN_CONFIG_PATH);
                FileUtils.forceMkdir(file);
                if (!file.canRead() || !file.canWrite()) {
                    return false;
                }
            } catch (SecurityException e) {
                return false;
            } catch (IOException e) {
                return false;
            }
            return true;
        } else if (SystemUtils.IS_OS_LINUX) {
            // TODO Need to implements this for linux.
            return false;
        }
        throw new UnsupportedOperationException(SystemUtils.OS_NAME + " not supported");
    }

    /**
     * Return the location of the System profile.
     * 
     * @return Return a directory.
     */
    private static String getWindowsSystemProfilePath() {
        if (SystemUtils.IS_OS_WINDOWS) {
            return System.getenv("WINDIR") + "/System32/config/systemprofile";
        }
        return null;
    }

    /**
     * Execute "reg.exe" with the given arguments.
     * 
     * @param args
     *            the arguments
     * @return the output of the command.
     * @throws APIException
     *             if the process didn't complete successfully.
     */
    public static String reg(String... args) throws APIException {
        List<String> command = new ArrayList<String>();
        command.add("reg.exe");
        if (args != null) {
            command.addAll(Arrays.asList(args));
        }
        LOGGER.debug("executing {}", StringUtils.join(command, " "));
        try {
            Process p = new ProcessBuilder().command(command).redirectErrorStream(true).start();
            StreamHandler sh = new StreamHandler(p);
            sh.start();
            if (p.waitFor() != 0) {
                throw new APIException(sh.getOutput());
            }
            return sh.getOutput();
        } catch (IOException e) {
            throw new APIException("fail to create subprocess", e);
        } catch (InterruptedException e) {
            // Swallow. Should no happen
            LOGGER.warn("process interupted", e);
            Thread.currentThread().interrupt();
            return null;
        }
    }

}
