package com.patrikdufresne.minarca.core;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.Writer;
import java.nio.charset.Charset;
import java.util.ArrayList;
import java.util.List;
import java.util.Properties;

import org.apache.commons.io.output.FileWriterWithEncoding;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Singleton class used to change the configuration of the backup.
 * 
 * @author ikus060
 * 
 */
public class Configurations {

	/**
	 * Property name.
	 */
	private static final String COMPUTERNAME = "computername";
	/**
	 * Filename used for configuration file. Notice, this is also read by batch
	 * file.
	 */
	private static final String CONF_FILENAME = "conf";

	/**
	 * Exclude filename.
	 */
	private static final String EXCLUDES_FILENAME = "includes";
	/**
	 * Includes filename.
	 */
	private static final String INCLUDES_FILENAME = "includes";
	static final transient Logger LOGGER = LoggerFactory
			.getLogger(Configurations.class);
	private static final String NEW_LINE = System.getProperty("line.separator");
	/**
	 * Property name.
	 */
	private static final String REMOTEHOST = "remotehost";

	/**
	 * Property name.
	 */
	private static final String USERNAME = "username";
	/**
	 * Reference to the configuration file.
	 */
	private File confFile;
	private File excludesFile;
	private File includesFile;

	/**
	 * Reference to the configuration.
	 */
	private Properties properties;

	/**
	 * Default constructor.
	 */
	protected Configurations(File configDir) {

		this.confFile = new File(configDir, CONF_FILENAME); //$NON-NLS-1$
		this.includesFile = new File(configDir, INCLUDES_FILENAME); //$NON-NLS-1$
		this.excludesFile = new File(configDir, EXCLUDES_FILENAME); //$NON-NLS-1$

		// Load the configuration
		this.properties = new Properties();
		try {
			FileInputStream in = new FileInputStream(confFile);
			this.properties.load(in);
			in.close();
		} catch (IOException e) {
			LoggerFactory.getLogger(Configurations.class).warn(
					"can't load properties {}", confFile);
		}
	}

	public String getComputername() {
		return this.properties.getProperty(COMPUTERNAME);
	}

	public List<String> getExcludes() throws IOException {
		return readPatterns(excludesFile);
	}

	public List<String> getIncludes() throws IOException {
		return readPatterns(includesFile);
	}

	public String getRemotehost() {
		return this.properties.getProperty(REMOTEHOST);
	}

	public String getUsername() {
		return this.properties.getProperty(USERNAME);
	}

	private List<String> readPatterns(File file) throws IOException {
		FileInputStream in = new FileInputStream(file);
		BufferedReader reader = new BufferedReader(new InputStreamReader(in,
				"ISO-8859-1"));
		List<String> list = new ArrayList<String>();
		String line;
		while ((line = reader.readLine()) != null) {
			if (line.startsWith("#")) {
				continue;
			}
			list.add(line);
		}
		reader.close();
		return list;
	}

	/**
	 * Used to persist the configuration.
	 * 
	 * @throws IOException
	 */
	public void save() throws IOException {
		Writer writer = new FileWriterWithEncoding(confFile,
				Charset.forName("ISO-8859-1"));
		this.properties.store(writer, "Backup configuration. Please do"
				+ "not change this configuration file manually.");
		writer.close();
	}

	public void setComputername(String value) {
		this.properties.setProperty(COMPUTERNAME, value);
	}

	public void setExcludes(List<String> patterns) throws IOException {
		writePatterns(excludesFile, patterns);
	}

	public void setIncludes(List<String> patterns) throws IOException {
		writePatterns(includesFile, patterns);
	}

	public void setRemotehost(String value) {
		this.properties.setProperty(REMOTEHOST, value);
	}

	public void setUsername(String value) {
		this.properties.setProperty(USERNAME, value);
	}

	private void writePatterns(File file, List<String> pattern)
			throws IOException {
		FileWriterWithEncoding writer = new FileWriterWithEncoding(file,
				"ISO-8859-1");
		for (String line : pattern) {
			writer.append(line);
			writer.append(NEW_LINE);
		}
		writer.close();
	}

}
