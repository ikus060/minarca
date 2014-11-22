package com.patrikdufresne.minarca.core;

import java.io.File;
import java.io.IOException;
import java.net.MalformedURLException;
import java.security.InvalidKeyException;
import java.security.KeyPair;
import java.security.NoSuchAlgorithmException;
import java.security.interfaces.RSAPublicKey;

import org.jsoup.helper.Validate;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.patrikdufresne.minarca.core.internal.InternalHttpClient;
import com.patrikdufresne.minarca.core.internal.Plink;
import com.patrikdufresne.minarca.core.internal.Keygen;

/**
 * Used to represent a connection to minarca. Either via HTTP or SSH or both.
 * 
 * @author ikus060
 * 
 */
public class Client {
	/**
	 * Base URL. TODO change this.
	 */
	private static final String BASE_URL = "http://rdiffweb.patrikdufresne.com";
	/**
	 * The logger.
	 */
	private static final transient Logger LOGGER = LoggerFactory
			.getLogger(Client.class);
	/**
	 * Locations page.
	 */
	private static final String PAGE_LOCATIONS = "/";
	/**
	 * The remote host.
	 */
	private static final String REMOTE_HOST = "fente.patrikdufresne.com";

	/**
	 * Reference to the internal HTTP client used to request pages.
	 */
	private InternalHttpClient http;
	private String password;

	private String username;

	/**
	 * Create a new minarca client.
	 * 
	 * @param username
	 *            the username
	 * @param password
	 *            the password.
	 * @throws APIException
	 * @throws MalformedURLException
	 */
	protected Client(String username, String password) throws APIException {
		this(BASE_URL, username, password);
	}

	/**
	 * Private constructor providing default URL.
	 * 
	 * @param url
	 * @throws APIException
	 */
	private Client(String url, String username, String password)
			throws APIException {
		Validate.notNull(this.username = username);
		Validate.notNull(this.password = password);
		// Check credentials by requesting the locations page.
		LOGGER.debug("authentication to minarca as {}", username);
		this.http = new InternalHttpClient(BASE_URL, username, password);
		this.http.get(PAGE_LOCATIONS);
	}

	/**
	 * Return the remote host to be used for SSH communication.
	 * <p>
	 * Current implementation return the same SSH server. In future, this
	 * implementation might changed to request the web server for a specific
	 * URL.
	 * 
	 * @return
	 */
	protected String getRemoteHost() {
		return REMOTE_HOST;
	}

	/**
	 * Register a new computer.
	 * <p>
	 * A successful link of this computer will generate a new configuration
	 * file.
	 * <p>
	 * This implementation will generate public and private keys for putty. The
	 * public key will be sent to minarca. The computer name is added to the
	 * comments.
	 * 
	 * 
	 * @param computername
	 *            friendly name to represent this computer.
	 * @throws APIException
	 *             if the keys can't be created.
	 * @throws IllegalAccessException
	 *             if the computer name is not valid.
	 */
	public void link(String computername) throws APIException {

		Validate.notNull(computername);
		Validate.notEmpty(computername);
		Validate.isTrue(computername.matches("[a-zA-Z][a-zA-Z0-9\\-\\.]*"));

		/*
		 * Generate the keys
		 */
		LOGGER.debug("generating public and private key for {}", computername);
		File idrsaFile = new File(API.getConfigDirFile(), "id_rsa.pub");
		File identityFile = new File(API.getConfigDirFile(), "key.ppk");
		try {
			// Generate a key pair.
			KeyPair pair = Keygen.generateRSA();
			// Generate a simple id_rsa.pub file.
			Keygen.toPublicIdRsa((RSAPublicKey) pair.getPublic(), computername,
					idrsaFile);
			// Generate a Putty private key file.
			Keygen.toPrivatePuttyKey(pair, computername, identityFile);
		} catch (NoSuchAlgorithmException e) {
			throw new APIException("fail to generate the keys", e);
		} catch (IOException e) {
			throw new APIException("fail to generate the keys", e);
		} catch (InvalidKeyException e) {
			throw new APIException("fail to generate the keys", e);
		}

		/*
		 * Share them via ssh.
		 */
		LOGGER.debug("sending public key trought SSH");
		Plink ssh = new Plink(getRemoteHost(), username, password, identityFile);
		ssh.sendPublicKey(idrsaFile);

		/*
		 * Generate configuration file.
		 */
		LOGGER.debug("saving configuration [{}][{}][{}]", computername,
				this.username, getRemoteHost());
		API.INSTANCE.setComputerName(computername);
		API.INSTANCE.setUsername(this.username);
		API.INSTANCE.setRemotehost(getRemoteHost());

	}

	/**
	 * Used to unlink this computer.
	 */
	public void unlink() {
		// TODO complete this method to unlink this computer
	}

}
