package com.patrikdufresne.minarca.core.internal;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import org.apache.commons.lang.StringUtils;
import org.apache.commons.lang3.SystemUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.patrikdufresne.minarca.core.APIException;
import com.patrikdufresne.minarca.core.APIException.MinarcaMissingException;

/**
 * Utility class to locate minarca executable and launch it.
 * 
 * @author Patrik Dufresne
 * 
 */
public class MinarcaExecutable {

    /**
     * The logger.
     */
    private static final transient Logger LOGGER = LoggerFactory.getLogger(MinarcaExecutable.class);

    /**
     * Executable launch to start backup.
     */
    public static final String MINARCA_EXE;

    /**
     * Property used to define the location of minarca.bat file.
     */
    private static final String PROPERTY_MINARCA_LOCATION = "minarca.exe.location";

    static {
        if (SystemUtils.IS_OS_WINDOWS) {
            if (SystemUtils.JAVA_VM_NAME.contains("64-Bit")) {
                MINARCA_EXE = "minarca64.exe";
            } else {
                MINARCA_EXE = "minarca.exe";
            }
        } else {
            MINARCA_EXE = "minarca";
        }
    }

    public MinarcaExecutable() {

    }

    /**
     * Return the location of minarca executable.
     * 
     * @return
     */
    public static File getMinarcaLocation() {
        return Compat.searchFile(MINARCA_EXE, System.getProperty(PROPERTY_MINARCA_LOCATION), "./bin/", ".", "/opt/minarca/bin/");
    }

    /**
     * Return the command line to be executed to run a backup.
     * 
     * @return
     * @throws APIException
     */
    public static String[] createMinarcaCommand(String... extraArgs) throws MinarcaMissingException {
        File file = getMinarcaLocation();
        if (file == null) {
            throw new MinarcaMissingException();
        }
        List<String> args = new ArrayList<String>();
        args.add(file.toString());
        args.addAll(Arrays.asList(extraArgs));
        return args.toArray(new String[0]);
    }

    /**
     * Return the command line as a single line.
     * 
     * @return
     * @throws APIException
     */
    public static String createMinarcaCommandLine(String... extraArgs) throws MinarcaMissingException {
        StringBuffer buf = new StringBuffer();
        for (String a : createMinarcaCommand(extraArgs)) {
            // Check if space is needed
            if (buf.length() > 0) {
                buf.append(" ");
            }
            // Check if quote are require.
            if (a.contains(" ")) {
                buf.append("'");
                buf.append(a);
                buf.append("'");
            } else {
                buf.append(a);
            }
        }
        return buf.toString();
    }

    /**
     * Used to start minarca executable to stop current instance.
     * 
     * @throws APIException
     */
    public void backup(boolean force) throws APIException {
        String command[];
        if (force) {
            command = createMinarcaCommand("--backup", "--force");
        } else {
            command = createMinarcaCommand("--backup");
        }
        execute(command);
    }

    /**
     * Used to start minarca executable to stop current instance.
     * 
     * @throws APIException
     */
    public void stop() throws APIException {
        // Need to stop the process.
        execute(createMinarcaCommand("--backup", "--stop"));
    }

    /**
     * Execute minarca proess. Don't wait for it.
     * 
     * @param command
     * @throws APIException
     */
    private void execute(String[] command) throws APIException {
        LOGGER.debug("executing command: {}", StringUtils.join(command, " "));
        try {
            new ProcessBuilder(command).inheritIO().start();
        } catch (IOException e) {
            throw new APIException(e);
        }
    }

}
