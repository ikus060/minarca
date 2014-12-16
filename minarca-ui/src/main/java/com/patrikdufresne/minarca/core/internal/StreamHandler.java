/*
 * Copyright (c) 2014, Patrik Dufresne Service Logiciel. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.core.internal;

import java.io.BufferedWriter;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.io.Writer;
import java.nio.charset.Charset;

import org.apache.commons.lang3.SystemUtils;
import org.jsoup.helper.Validate;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Used to answer the password for putty process.
 * 
 * @author Patrik Dufresne
 * 
 */
public class StreamHandler extends Thread {

    private static final int CR = 10;

    private static final int LF = 13;
    /**
     * Logger
     */
    private static final transient Logger LOGGER = LoggerFactory.getLogger(StreamHandler.class);
    /**
     * Data return from the process execution.
     */
    private StringBuilder output = new StringBuilder();
    /**
     * Process to monitor.
     */
    private final Process p;

    /**
     * Password value to answer.
     */
    private final String password;
    /**
     * Charset used to read process output.
     */
    private final Charset charset;

    /**
     * Process stream handler.
     * 
     * @param p
     *            the process.
     */
    public StreamHandler(Process p) {
        this(p, null, ProcessCharset.defaultCharset());
    }

    /**
     * Process stream handler.
     * 
     * @param p
     *            the process
     * @param charset
     *            the charset to be used.
     */
    public StreamHandler(Process p, Charset charset) {
        this(p, null, charset);
    }

    /**
     * Process stream handler.
     * 
     * @param p
     *            the process
     * @param password
     *            the password
     */
    public StreamHandler(Process p, String password) {
        this(p, password, ProcessCharset.defaultCharset());
    }

    /**
     * The process to be linked to.
     * 
     * @param p
     */
    public StreamHandler(Process p, String password, Charset charset) {
        Validate.notNull(this.p = p);
        this.password = password;
        Validate.notNull(this.charset = charset);
    }

    /**
     * Get data return by plink.
     * 
     * @return
     */
    public String getOutput() {
        synchronized (output) {
            return output.toString();
        }
    }

    @Override
    public void run() {
        synchronized (output) {
            boolean answered = false;
            // Read stream line by line without buffer (otherwise it block).
            try {
                Writer out = new BufferedWriter(new OutputStreamWriter(this.p.getOutputStream()));
                InputStreamReader in = new InputStreamReader(this.p.getInputStream(), charset);

                if (password == null) {
                    out.close();
                }

                StringBuilder buf = new StringBuilder();
                int b;
                while ((b = in.read()) != -1) {
                    // Write the byte into a buffer
                    if (b == CR || b == LF) {
                        String line = buf.toString();
                        if (!line.isEmpty()) {
                            LOGGER.debug(line);
                            output.append(line);
                            output.append(SystemUtils.LINE_SEPARATOR);
                        }
                        buf.setLength(0);
                    } else {
                        buf.append((char) b);
                    }
                    if (!answered && this.password != null) {
                        String prompt = buf.toString();
                        //
                        if (prompt.endsWith("password: ")) {
                            LOGGER.debug(prompt);
                            out.append(password);
                            out.append(SystemUtils.LINE_SEPARATOR);
                            out.flush();
                            out.close();
                            // Reset the buffer
                            buf.setLength(0);
                            answered = true;
                        }
                        // Check if asking for finger print confirmation.
                        if (prompt.contains("Store key in cache? (y/n)")) {
                            // Press enter to abandon.
                            out.append(SystemUtils.LINE_SEPARATOR);
                            out.flush();
                            buf.setLength(0);
                        }
                    }
                }
            } catch (IOException e) {
                LOGGER.warn("unknown IO error", e);
            }
        }
    }
}