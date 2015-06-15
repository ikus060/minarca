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

    /**
     * Interface used to allow client to send data to the stream.
     * 
     * @author Patrik Dufresne
     * 
     */
    public interface PromptHandler {

        /**
         * Called everytime the prompt is updated (may be called for each new char added to the stream.)
         * 
         * @param prompt
         *            the current prompt line.
         * @return The value to be send (or null if nothing to sent).
         */
        public String handle(String prompt);

    }

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
     * Charset used to read process output.
     */
    private final Charset charset;
    /**
     * Use to prompt.
     */
    private PromptHandler handler;

    /**
     * Process stream handler.
     * 
     * @param p
     *            the process.
     */
    public StreamHandler(Process p) {
        this(p, Compat.CHARSET_PROCESS, null);
    }

    public StreamHandler(Process p, PromptHandler handler) {
        this(p, Compat.CHARSET_PROCESS, handler);
    }

    public StreamHandler(Process p, Charset charset) {
        this(p, charset, null);
    }

    /**
     * The process to be linked to.
     * 
     * @param p
     */
    public StreamHandler(Process p, Charset charset, PromptHandler handler) {
        Validate.notNull(this.p = p);
        Validate.notNull(this.charset = charset);
        this.handler = handler;
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
            // Read stream line by line without buffer (otherwise it block).
            try {
                Writer out = new BufferedWriter(new OutputStreamWriter(this.p.getOutputStream()));
                if (handler == null) {
                    out.close();
                }

                InputStreamReader in = new InputStreamReader(this.p.getInputStream(), charset);

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
                    if (handler != null) {
                        String prompt = buf.toString();
                        String answer = handler.handle(prompt);
                        if (answer != null) {
                            LOGGER.debug(prompt);
                            // LOGGER.debug(answer);
                            out.append(answer);
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