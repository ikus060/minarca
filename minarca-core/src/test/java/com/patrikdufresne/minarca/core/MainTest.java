/**
 * Copyright(C) 2013 Patrik Dufresne Service Logiciel <info@patrikdufresne.com>
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *         http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.patrikdufresne.minarca.core;

import static org.junit.Assert.*;

import java.io.ByteArrayOutputStream;
import java.io.PrintStream;
import java.security.Permission;
import java.util.Locale;

import org.junit.After;
import org.junit.Before;
import org.junit.Ignore;
import org.junit.Rule;
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
        assertTrue(outContent.toString().contains("include **/test"));
        assertTrue(outContent.toString().contains("exclude **/me"));
        assertTrue(!outContent.toString().contains("include **/toberemove"));
        assertTrue(outContent.toString().contains("exclude **/toberemove"));
    }

}
