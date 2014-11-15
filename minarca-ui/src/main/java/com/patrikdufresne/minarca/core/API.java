package com.patrikdufresne.minarca.core;

import java.io.File;
import java.net.InetAddress;
import java.net.UnknownHostException;

import org.apache.commons.lang.StringUtils;

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
	 * Return the location of the configuration.
	 * 
	 * @return
	 */
	public static File getConfigDir() {
		String osName = System.getProperty("os.name"); //$NON-NLS-1$
		String homeDir = System.getProperty("user.home"); //$NON-NLS-1$
		if (osName.equals("Linux")) { //$NON-NLS-1$
			File configDir = new File(homeDir, ".config/" + APPNAME); //$NON-NLS-1$
			configDir.mkdirs();
			return configDir;
		} else {
			File configDir = new File(homeDir, "AppData/" + APPNAME); //$NON-NLS-1$
			configDir.mkdirs();
			return configDir;
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
	 * Return a default computer name to represent this computer.
	 * <p>
	 * Current implementation gets the hostname.
	 * 
	 * @return an empty string or a hostname
	 */
	public String getDefaultComputerName() {
		// For windows
		String host = System.getenv("COMPUTERNAME");
		if (host != null)
			return host;
		// For linux
		host = System.getenv("HOSTNAME");
		if (host != null)
			return host;

		try {
			String result = InetAddress.getLocalHost().getHostName();
			if (StringUtils.isNotEmpty(result))
				return result;
		} catch (UnknownHostException e) {
			// failed; try alternate means.
		}

		return "";
	}

	private Configurations config = new Configurations(getConfigDir());

	public Configurations getConfigurations() {
		return this.config;
	}

	/**
	 * Check if the backup is configured.
	 * 
	 * @return True if configured. False otherwise.
	 */
	public boolean isConfigured() {
		return StringUtils.isNotEmpty(config.getComputername())
				&& StringUtils.isNotEmpty(config.getRemotehost())
				&& StringUtils.isNotEmpty(config.getUsername());
	}

}
