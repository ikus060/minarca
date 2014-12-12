/*
 * Copyright (c) 2014, Patrik Dufresne Service Logiciel. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.core.internal;

import java.io.BufferedWriter;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStreamWriter;
import java.io.Writer;

import org.apache.commons.lang3.SystemUtils;
import org.jsoup.helper.Validate;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.patrikdufresne.minarca.core.API;

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
    private StringBuilder buf = new StringBuilder();
    /**
     * Process to monitor.
     */
    private Process p;

    /**
     * Password value to answer.
     */
    private String password;

    /**
     * Process stream handler.
     * 
     * @param p
     */
    public StreamHandler(Process p) {
        this(p, null);
    }

    /**
     * The process to be linked to.
     * 
     * @param p
     */
    public StreamHandler(Process p, String password) {
        Validate.notNull(this.p = p);
        this.password = password;
    }

    /**
     * Get data return by plink.
     * 
     * @return
     */
    public String getOutput() {
        synchronized (buf) {
            return buf.toString();
        }
    }

    @Override
    public void run() {
        synchronized (buf) {
            boolean answered = false;
            boolean validFingerPrint = false;
            Writer out = new BufferedWriter(new OutputStreamWriter(this.p.getOutputStream()));
            InputStream in = this.p.getInputStream();
            // Read stream line by line without buffer (otherwise it block).
            try {
                ByteArrayOutputStream data = new ByteArrayOutputStream();
                int b;
                while ((b = in.read()) != -1) {
                    // Write the byte into a buffer
                    if (b == CR || b == LF) {
                        String line = new String(data.toByteArray());
                        if (!line.isEmpty()) {
                            LOGGER.debug(line);
                            buf.append(line);
                            buf.append(SystemUtils.LINE_SEPARATOR);
                        }
                        data.reset();
                    } else {
                        data.write(b);
                    }
                    if (!answered && this.password != null) {
                        String prompt = new String(data.toByteArray());
                        //
                        if (prompt.endsWith("password: ")) {
                            LOGGER.debug(prompt);
                            out.append(password);
                            out.append(SystemUtils.LINE_SEPARATOR);
                            out.flush();
                            // Reset the buffer
                            data.reset();
                            answered = true;
                        }
                        // Plink might ask us to accept a fingerprint.
                        for (String fp : API.DEFAULT_REMOTEHOST_FINGERPRINT) {
                            if (prompt.contains(fp)) {
                                validFingerPrint = true;
                            }
                        }
                        // Check if asking for finger print confirmation.
                        if (prompt.contains("Store key in cache? (y/n)")) {
                            // Press enter to abandon.
                            if (validFingerPrint) {
                                out.append("y");
                            }
                            out.append(SystemUtils.LINE_SEPARATOR);
                            out.flush();
                            data.reset();
                        }
                    }
                }
            } catch (IOException e) {
                LOGGER.warn("unknown IO error", e);
            }
        }
    }
}