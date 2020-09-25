/*
 * Copyright (C) 2020, IKUS Software inc. All rights reserved.
 * IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.core;

import static org.junit.Assert.*;

import java.io.ByteArrayOutputStream;
import java.io.PrintStream;
import java.security.Permission;

import org.apache.commons.lang3.SystemUtils;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;

public class MainTest {

    /**
     * This exception should be raised instead of exiting the Jvm.
     * 
     * @author Patrik Dufresne
     * 
     */
    protected static class ExitException extends SecurityException {
        public final int status;

        public ExitException(int status) {
            super();
            this.status = status;
        }
    }

    /**
     * A security manager to raise the ExitException when calling System.exit().
     * 
     * @author Patrik Dufresne
     * 
     */
    private static class NoExitSecurityManager extends SecurityManager {
        @Override
        public void checkPermission(Permission perm) {
            // allow anything.
        }

        @Override
        public void checkPermission(Permission perm, Object context) {
            // allow anything.
        }

        @Override
        public void checkExit(int status) {
            super.checkExit(status);
            throw new ExitException(status);
        }
    }

    private final ByteArrayOutputStream outContent = new ByteArrayOutputStream();
    private final ByteArrayOutputStream errContent = new ByteArrayOutputStream();
    private final PrintStream originalOut = System.out;
    private final PrintStream originalErr = System.err;

    @Before
    public void setUpStreams() {
        System.setOut(new PrintStream(outContent));
        System.setErr(new PrintStream(errContent));
        System.setSecurityManager(new NoExitSecurityManager());
    }

    @After
    public void restoreStreams() {
        System.setOut(originalOut);
        System.setErr(originalErr);
        System.setSecurityManager(null);
    }

    /**
     * Call help.
     */
    @Test
    public void testMainHelp() {
        Main.main(new String[] { "--help" });
        assertTrue(!outContent.toString().isEmpty());
        assertTrue(outContent.toString().contains("Usage:"));
    }

    /**
     * Call version.
     */
    @Test
    public void testMainVersion() {
        Main.main(new String[] { "--version" });
        assertTrue(outContent.toString().contains("version"));
        assertTrue(outContent.toString().contains(API.getCurrentVersion()));
    }

    /**
     * Call version.
     */
    @Test
    public void testMainStatus() {
        Main.main(new String[] { "status" });
        assertTrue(outContent.toString().contains("Last backup:"));
        assertTrue(outContent.toString().contains("Connectivity status:"));
    }

    /**
     * Call include / exclude patterns.
     */
    @Test
    public void testMainPatterns() {
        // Call Include
        Main.main(new String[] { "patterns", "--clear" });
        Main.main(new String[] { "include", "**/test1" });
        Main.main(new String[] { "include", "**/toberemove" });
        Main.main(new String[] { "exclude", "**/me" });
        Main.main(new String[] { "exclude", "**/toberemove" });

        Main.main(new String[] { "patterns" });
        if (SystemUtils.IS_OS_WINDOWS) {
            assertTrue(outContent.toString().contains("include **\\test"));
            assertTrue(outContent.toString().contains("exclude **\\me"));
            assertTrue(!outContent.toString().contains("include **\\toberemove"));
            assertTrue(outContent.toString().contains("exclude **\\toberemove"));
        } else {
            assertTrue(outContent.toString().contains("include **/test"));
            assertTrue(outContent.toString().contains("exclude **/me"));
            assertTrue(!outContent.toString().contains("include **/toberemove"));
            assertTrue(outContent.toString().contains("exclude **/toberemove"));
        }

    }

    /**
     * Call with <code>minarca link --name</code>
     */
    @Test
    public void testParseArgumentsWithMissingValue() {
        assertNull(Main.parseArgument(new String[] { "link", "--name" }, false, null, "--name", "-n"));
    }

}
