package com.patrikdufresne.minarca.core;

import static com.patrikdufresne.minarca.Localized._;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.Writer;
import java.net.InetAddress;
import java.net.UnknownHostException;
import java.nio.charset.Charset;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Properties;

import org.apache.commons.io.output.FileWriterWithEncoding;
import org.apache.commons.lang.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.patrikdufresne.minarca.core.APIException.MissConfiguredException;
import com.patrikdufresne.minarca.core.APIException.NotConfiguredException;
import com.patrikdufresne.minarca.core.internal.Schtasks;

/**
 * This class is the main entry point to do everything related to minarca.
 * 
 * @author ikus060
 * 
 */
public enum API {
	INSTANCE;
	/**
	 * Application name used for sub folder
	 */
	private static final String APPNAME = "minarca";
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
	private static final String EXCLUDES_FILENAME = "excludes";

	/**
	 * Includes filename.
	 */
	private static final String INCLUDES_FILENAME = "includes";

	/**
	 * The logger.
	 */
	private static final transient Logger LOGGER = LoggerFactory
			.getLogger(API.class);

	/**
	 * Executable script to run backup.
	 */
	private static final String MINARCA_BATCH = "minarca.bat";

	/**
	 * New line separator.
	 */
	private static final String NEW_LINE = System.getProperty("line.separator");

	/**
	 * Property used to define the location of minarca.bat file.
	 */
	private static final String PROPERTY_MINARCA_BATCH_LOCATION = "minarca.bat.location";

	/**
	 * Property name.
	 */
	private static final String REMOTEHOST = "remotehost";

	private static final String TASK_NAME = "minarca backup";

	/**
	 * Property name.
	 */
	private static final String USERNAME = "username";

	/**
	 * Return the location of the configuration.
	 * 
	 * @return return a File instance.
	 */
	public static File getConfigDirFile() {
		String osName = System.getProperty("os.name"); //$NON-NLS-1$
		String homeDir = System.getProperty("user.home"); //$NON-NLS-1$
		if (osName.equals("Linux")) { //$NON-NLS-1$
			File configDir = new File(homeDir, ".config/" + APPNAME); //$NON-NLS-1$
			configDir.mkdirs();
			return configDir;
		} else {
			File configDir = new File(homeDir, "AppData/Local/" + APPNAME); //$NON-NLS-1$
			configDir.mkdirs();
			return configDir;
		}
	}

	/**
	 * Return a default computer name to represent this computer.
	 * <p>
	 * Current implementation gets the hostname.
	 * 
	 * @return an empty string or a hostname
	 */
	public static String getDefaultComputerName() {
		// For windows
		String host = System.getenv("COMPUTERNAME");
		if (host != null)
			return host.toLowerCase();
		// For linux
		host = System.getenv("HOSTNAME");
		if (host != null)
			return host.toLowerCase();

		try {
			String result = InetAddress.getLocalHost().getHostName();
			if (StringUtils.isNotEmpty(result))
				return result.toLowerCase();
		} catch (UnknownHostException e) {
			// failed; try alternate means.
		}
		return "";
	}

	public static List<GlobPattern> getDefaultExcludes() {
		String osName = System.getProperty("os.name");
		if (osName.equals("Linux")) { //$NON-NLS-1$
			return Arrays.asList(new GlobPattern(".*"), new GlobPattern("*~"));
		}
		String userHome = System.getProperty("user.home");
		List<GlobPattern> list = new ArrayList<GlobPattern>();
		list.add(new GlobPattern("**/pagefile.sys"));
		list.add(new GlobPattern("**/NTUSER.DAT*"));
		list.add(new GlobPattern("**/desktop.ini"));
		list.add(new GlobPattern("**/ntuser.ini"));
		list.add(new GlobPattern("**/Thumbs.db"));
		list.add(new GlobPattern("**/Default.rdp"));
		list.add(new GlobPattern("**/ntuser.dat*"));
		list.add(new GlobPattern("C:/Recovery/"));
		String windowDir = System.getenv("SystemRoot");
		if (windowDir != null) {
			list.add(new GlobPattern(windowDir));
		}
		String temp = System.getenv("TEMP");
		if (temp != null) {
			list.add(new GlobPattern(temp));
		}
		list.add(new GlobPattern(userHome + "/AppData/"));
		list.add(new GlobPattern(userHome + "/Tracing/"));
		return list;

	}

	public static List<GlobPattern> getDefaultIncludes() {
		// Return user directory.
		return Arrays.asList(new GlobPattern(System.getProperty("user.home")));
	}

	/**
	 * Reference to the configuration file.
	 */
	private File confFile;
	/**
	 * Reference to exclude file list.
	 */
	private File excludesFile;

	/**
	 * Reference to include file list.
	 */
	private File includesFile;

	/**
	 * Reference to the configuration.
	 */
	private Properties properties;

	/**
	 * Default constructor.
	 */
	private API() {

		File configDir = getConfigDirFile();
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
			LoggerFactory.getLogger(API.class).warn(
					_("can't load properties {}"), confFile);
		}
	}

	/**
	 * Used to check if the configuration is OK. Called as a sanity check to
	 * make sure "minarca" is properly configured. If not, it throw an
	 * exception.
	 * 
	 * @return
	 */
	public void checkConfig() throws APIException {
		// Basic sanity check to make sure it's configured. If not, display the
		// setup dialog.
		if (StringUtils.isEmpty(getComputername())
				|| StringUtils.isEmpty(getRemotehost())
				|| StringUtils.isEmpty(getUsername())) {
			throw new NotConfiguredException(_("minarca is not configured"));
		}
		if (getIncludes().isEmpty() || getExcludes().isEmpty()) {
			throw new MissConfiguredException(
					_("includes or excludes pattern are missing"));
		}
		if (!new Schtasks().exists(TASK_NAME)) {
			throw new MissConfiguredException(_("scheduled tasks is missing"));
		}
	}

	/**
	 * Establish connection to minarca.
	 * 
	 * @return a new client
	 * @throws APIException
	 */
	public Client connect(String username, String password) throws APIException {
		return new Client(username, password);
	}

	/**
	 * This method is called to sets the default configuration for includes,
	 * excludes and scheduled task.
	 * 
	 * @throws APIException
	 */
	public void defaultConfig() throws APIException {
		LOGGER.debug("restore default config");
		// Sets the default includes / excludes.
		setIncludes(getDefaultIncludes());
		setExcludes(getDefaultExcludes());

		// Delete & create schedule tasks.
		Schtasks scheduler = new Schtasks();
		if (scheduler.exists(TASK_NAME)) {
			scheduler.delete(TASK_NAME);
		}
		scheduler.create(TASK_NAME, getBackupCommand().getAbsolutePath());
	}

	/**
	 * Return the command line to be executed to run a backup.
	 * 
	 * @return
	 * @throws APIException
	 */
	private File getBackupCommand() throws APIException {
		List<String> locations = new ArrayList<String>();
		String value = System.getProperty(PROPERTY_MINARCA_BATCH_LOCATION);
		if (value != null) {
			locations.add(value);
		}
		locations.add(".");
		for (String location : locations) {
			File batch = new File(location, MINARCA_BATCH);
			if (batch.isFile() && batch.canRead()) {
				return batch;
			}
		}
		throw new APIException(_("{} is missing ", MINARCA_BATCH));
	}

	/**
	 * Friently named used to represent the computer being backuped.
	 * 
	 * @return the computer name.
	 */
	public String getComputername() {
		return this.properties.getProperty(COMPUTERNAME);
	}

	/**
	 * Return the exclude patterns used for the backup.
	 * 
	 * @return the list of pattern.
	 */
	public List<GlobPattern> getExcludes() {
		try {
			return readPatterns(excludesFile);
		} catch (IOException e) {
			LOGGER.warn("error reading excludes patterns", e);
			return Collections.emptyList();
		}
	}

	/**
	 * Return the include patterns used for the backup.
	 * 
	 * @return the list of pattern.
	 */
	public List<GlobPattern> getIncludes() {
		try {
			return readPatterns(includesFile);
		} catch (IOException e) {
			LOGGER.warn("error reading includes patterns", e);
			return Collections.emptyList();
		}
	}

	/**
	 * Get the remote host used for the backup (SSH server).
	 * 
	 * @return the hostname.
	 */
	public String getRemotehost() {
		return this.properties.getProperty(REMOTEHOST);
	}

	/**
	 * Get the username used for the backup (username used to authentication
	 * with SSH server).
	 * 
	 * @return
	 */
	public String getUsername() {
		return this.properties.getProperty(USERNAME);
	}

	/**
	 * Internal method used to read patterns.
	 * 
	 * @param file
	 * @return
	 * @throws IOException
	 */
	private List<GlobPattern> readPatterns(File file) throws IOException {
		FileInputStream in = new FileInputStream(file);
		BufferedReader reader = new BufferedReader(new InputStreamReader(in,
				"ISO-8859-1"));
		List<GlobPattern> list = new ArrayList<GlobPattern>();
		String line;
		while ((line = reader.readLine()) != null) {
			if (line.startsWith("#")) {
				continue;
			}
			try {
				list.add(new GlobPattern(line));
			} catch (IllegalArgumentException e) {
				// Swallow
				LOGGER.warn("invalid pattern [{}] discarded", line);
			}
		}
		reader.close();
		return list;
	}

	/**
	 * Used to persist the configuration.
	 * 
	 * @throws IOException
	 */
	private void save() throws IOException {
		Writer writer = new FileWriterWithEncoding(confFile,
				Charset.forName("ISO-8859-1"));
		this.properties.store(writer, "Backup configuration. Please do "
				+ "not change this configuration file manually.");
		writer.close();
	}

	/**
	 * Sets the computer name.
	 * 
	 * @param value
	 * @throws APIException
	 */
	public void setComputerName(String value) throws APIException {
		this.properties.setProperty(COMPUTERNAME, value);
		try {
			save();
		} catch (IOException e) {
			throw new APIException(_("fail to save config"), e);
		}
	}

	/**
	 * Sets a new exclude patern list.
	 * 
	 * @param patterns
	 * @throws APIException
	 */
	public void setExcludes(List<GlobPattern> patterns) throws APIException {
		try {
			writePatterns(excludesFile, patterns);
		} catch (IOException e) {
			throw new APIException(_("fail to save config"), e);
		}
	}

	/**
	 * Sets a new include pattern list.
	 * 
	 * @param patterns
	 * @throws APIException
	 */
	public void setIncludes(List<GlobPattern> patterns) throws APIException {
		try {
			writePatterns(includesFile, patterns);
		} catch (IOException e) {
			throw new APIException(_("fail to save config"), e);
		}
	}

	/**
	 * Sets remote host.
	 * 
	 * @param value
	 * @throws APIException
	 */
	public void setRemotehost(String value) throws APIException {
		this.properties.setProperty(REMOTEHOST, value);
		try {
			save();
		} catch (IOException e) {
			throw new APIException(_("fail to save config"), e);
		}
	}

	/**
	 * Sets the username.
	 * 
	 * @param value
	 * @throws APIException
	 */
	public void setUsername(String value) throws APIException {
		this.properties.setProperty(USERNAME, value);
		try {
			save();
		} catch (IOException e) {
			throw new APIException(_("fail to save config"), e);
		}
	}

	/**
	 * Internal method used to write the patterns into a file.
	 * 
	 * @param file
	 * @param pattern
	 * @throws IOException
	 */
	private void writePatterns(File file, List<GlobPattern> pattern)
			throws IOException {
		FileWriterWithEncoding writer = new FileWriterWithEncoding(file,
				"ISO-8859-1");
		for (GlobPattern line : pattern) {
			writer.append(line.toString());
			writer.append(NEW_LINE);
		}
		writer.close();
	}

}
