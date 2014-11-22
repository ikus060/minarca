package com.patrikdufresne.minarca.core.internal;

import java.io.BufferedWriter;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStreamWriter;
import java.io.Writer;

import org.jsoup.helper.Validate;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Used to answer the password for putty process.
 * 
 * @author ikus060-vm
 *
 */
public class StreamHandler extends Thread {

	private static final int CR = 10;

	private static final int LF = 13;
	/**
	 * Logger
	 */
	private static final transient Logger LOGGER = LoggerFactory
			.getLogger(StreamHandler.class);
	/**
	 * New line separator
	 */
	private static final String NEWLINE = System.getProperty("line.separator");
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
		return buf.toString();
	}

	@Override
	public void run() {
		boolean answered = false;
		Writer out = new BufferedWriter(new OutputStreamWriter(
				this.p.getOutputStream()));
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
						buf.append(NEWLINE);
					}
					data.reset();
				} else {
					data.write(b);
				}
				if (!answered && this.password != null) {
					String prompt = new String(data.toByteArray());
					if (prompt.endsWith("password: ")) {
						LOGGER.debug(prompt);
						out.append(password);
						out.append(NEWLINE);
						out.flush();
						// Reset the buffer
						data.reset();
						answered = true;
					}
				}
			}
		} catch (IOException e) {
			LOGGER.warn("unknown IO error", e);
		}

	}
}
