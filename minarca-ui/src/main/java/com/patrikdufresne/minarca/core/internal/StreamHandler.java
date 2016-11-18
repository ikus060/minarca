/*
 * Copyright (C) 2015, Patrik Dufresne Service Logiciel inc. All rights reserved.
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
import java.util.concurrent.Callable;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;

import org.apache.commons.lang3.SystemUtils;
import org.apache.commons.lang3.Validate;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.google.common.util.concurrent.ThreadFactoryBuilder;

/**
 * Used to answer the password for putty process.
 * 
 * @author Patrik Dufresne
 * 
 */
public class StreamHandler {

    private class PrivateCallable implements Callable<String> {
        @Override
        public String call() throws Exception {
            // Data return from the process execution.
            StringBuilder output = new StringBuilder();
            // Read stream line by line without buffer (otherwise it block).
            try {
                Writer out = new BufferedWriter(new OutputStreamWriter(p.getOutputStream()));
                if (handler == null) {
                    out.close();
                }

                InputStreamReader in = new InputStreamReader(p.getInputStream(), charset);

                StringBuilder buf = new StringBuilder();
                int b;
                while ((b = in.read()) != -1) {
                    // Write the byte into a buffer
                    if (b == CR || b == LF) {
                        String line = buf.toString();
                        if (!line.isEmpty()) {
                            log(line);
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
                            log(prompt);
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
            return output.toString();
        }
    }

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
     * Charset used to read process output.
     */
    private final Charset charset;
    /**
     * Executor service used to read the stream.
     */
    private ExecutorService executor = Executors.newFixedThreadPool(1, new ThreadFactoryBuilder().setNameFormat("stream-handler-%d").build());
    /**
     * LogLevel
     */
    private boolean forceLog;

    private Future<String> future;
    /**
     * Use to prompt.
     */
    private PromptHandler handler;

    /**
     * Process to monitor.
     */
    private final Process p;

    /**
     * Process stream handler.
     * 
     * @param p
     *            the process.
     */
    public StreamHandler(Process p) {
        this(p, Compat.CHARSET_PROCESS, null, false);
    }

    public StreamHandler(Process p, Charset charset) {
        this(p, charset, null, false);
    }

    /**
     * The process to be linked to.
     * 
     * @param p
     */
    public StreamHandler(Process p, Charset charset, PromptHandler handler, boolean forceLog) {
        Validate.notNull(this.p = p);
        Validate.notNull(this.charset = charset);
        this.handler = handler;
        this.forceLog = forceLog;
        this.future = this.executor.submit(new PrivateCallable());
        // Once the task is submit, we may shutdown the executor.
        this.executor.shutdown();
    }

    public StreamHandler(Process p, PromptHandler handler) {
        this(p, Compat.CHARSET_PROCESS, handler, false);
    }

    /**
     * Get data return by the stream.
     * 
     * @return the content of the stream.
     */
    public String getOutput() {
        try {
            return this.future.get();
        } catch (InterruptedException e) {
            LOGGER.warn("stream handler was interupted", e);
        } catch (ExecutionException e) {
            LOGGER.warn("fail to get stream value", e);
        }
        return "";
    }

    /**
     * Log a line into log file.
     * 
     * @param line
     */
    private void log(String line) {
        if (forceLog) {
            if (LOGGER.isDebugEnabled()) {
                LOGGER.debug(line);
            } else if (LOGGER.isInfoEnabled()) {
                LOGGER.info(line);
            } else if (LOGGER.isWarnEnabled()) {
                LOGGER.warn(line);
            } else if (LOGGER.isErrorEnabled()) {
                LOGGER.error(line);
            }
        } else {
            LOGGER.trace(line);
        }
    }
}