package com.patrikdufresne.minarca.core;

import java.io.BufferedReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.UnsupportedEncodingException;
import java.net.CookieHandler;
import java.net.CookieManager;
import java.net.MalformedURLException;
import java.security.InvalidKeyException;
import java.security.KeyPair;
import java.security.NoSuchAlgorithmException;
import java.security.interfaces.RSAPrivateKey;
import java.security.interfaces.RSAPublicKey;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;

import org.apache.http.HttpResponse;
import org.apache.http.NameValuePair;
import org.apache.http.client.ClientProtocolException;
import org.apache.http.client.HttpClient;
import org.apache.http.client.entity.UrlEncodedFormEntity;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.client.methods.HttpPost;
import org.apache.http.impl.client.DefaultHttpClient;
import org.apache.http.message.BasicNameValuePair;
import org.jsoup.Jsoup;
import org.jsoup.helper.Validate;
import org.jsoup.nodes.Document;
import org.jsoup.select.Elements;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.patrikdufresne.minarca.ui.setup.SetupDialog;

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
	 * Locations page.
	 */
	private static final String PAGE_LOCATIONS = "/";
	/**
	 * The logger.
	 */
	private static final transient Logger LOGGER = LoggerFactory
			.getLogger(SetupDialog.class);
	/**
	 * Login page.
	 */
	private static final String PAGE_LOGIN = "/login/";

	/**
	 * Token to look for to distinct login page.
	 */
	private static final String LOGIN_TOKEN = "id=\"form-login\"";

	static {
		CookieHandler.setDefault(new CookieManager());
	}

	/**
	 * Check if the page return any error.
	 * 
	 * @throws APIException
	 */
	private static void checkPage(String page) throws APIException {
		// Check error
		Document doc = Jsoup.parse(page);
		Elements elements = doc.getElementsByAttributeValueContaining("class",
				"alert-danger");
		if (elements.size() > 0) {
			throw new APIException.ApplicationException(elements.get(0).html());
		}
		elements = doc.getElementsByAttributeValueContaining("class",
				"alert-warning");
		if (elements.size() > 0) {
			throw new APIException.ApplicationException(elements.get(0).html());
		}
	}

	/**
	 * Effective base url.
	 */
	private String baseurl;

	private HttpClient client = new DefaultHttpClient();

	private String cookies;

	private String password;

	private final String USER_AGENT = "Mozilla/5.0";

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
	 * Private construtor providing default URL.
	 * 
	 * @param url
	 * @throws APIException
	 */
	private Client(String url, String username, String password)
			throws APIException {
		Validate.notNull(this.baseurl = url);
		Validate.notNull(this.username = username);
		Validate.notNull(this.password = password);

		// Check credential with simple login.
		get(PAGE_LOCATIONS);
	}

	/**
	 * Execute the HTTP GET.
	 * 
	 * @throws APIException
	 */
	private String get(String url) throws APIException {
		String page;
		try {
			page = getPageContent(baseurl + url);
			if (page.contains(LOGIN_TOKEN)) {
				page = sendPost(BASE_URL + PAGE_LOGIN,
						createLoginParams(this.username, this.password));
			}
		} catch (IOException e) {
			throw new APIException(e);
		}
		checkPage(page);
		return page;
	}

	private List<NameValuePair> createLoginParams(String username,
			String password) throws UnsupportedEncodingException {
		List<NameValuePair> paramList = new ArrayList<NameValuePair>();
		paramList.add(new BasicNameValuePair("login", username));
		paramList.add(new BasicNameValuePair("password", password));
		return paramList;
	}

	private String getPageContent(String url) throws ClientProtocolException,
			IOException, APIException {

		HttpGet request = new HttpGet(url);

		request.setHeader("User-Agent", USER_AGENT);
		request.setHeader("Accept",
				"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8");
		request.setHeader("Accept-Language", "en-US,en;q=0.5");

		HttpResponse response = client.execute(request);
		int responseCode = response.getStatusLine().getStatusCode();

		LOGGER.trace("Sending 'GET' request to URL : {}", url);
		System.out.println("Response Code : " + responseCode);

		BufferedReader rd = new BufferedReader(new InputStreamReader(response
				.getEntity().getContent()));

		StringBuffer result = new StringBuffer();
		String line = "";
		while ((line = rd.readLine()) != null) {
			result.append(line);
		}

		// set cookies
		this.cookies = response.getFirstHeader("Set-Cookie") == null ? ""
				: response.getFirstHeader("Set-Cookie").toString();

		if (responseCode != 200) {
			throw new APIException(result.toString());
		}

		return result.toString();

	}

	private String post(String url, Map<String, String> data)
			throws ClientProtocolException, IOException, APIException {
		// Build the post data.
		List<NameValuePair> postParams = new ArrayList<NameValuePair>();
		for (Entry<String, String> e : data.entrySet()) {
			postParams.add(new BasicNameValuePair(e.getKey(), e.getValue()));
		}

		String page = sendPost(BASE_URL + url, postParams);
		if (page.contains(LOGIN_TOKEN)) {
			page = sendPost(BASE_URL + PAGE_LOGIN,
					createLoginParams(this.username, this.password));
			checkPage(page);
			page = sendPost(BASE_URL + url, postParams);
		}

		checkPage(page);

		return page;
	}

	private String sendPost(String url, List<NameValuePair> postParams)
			throws ClientProtocolException, IOException, APIException {

		HttpPost post = new HttpPost(url);

		// add header
		post.setHeader("User-Agent", USER_AGENT);
		post.setHeader("Accept",
				"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8");
		post.setHeader("Accept-Language", "en-US,en;q=0.5");
		post.setHeader("Cookie", this.cookies);
		post.setHeader("Connection", "keep-alive");
		post.setHeader("Referer", BASE_URL);
		post.setHeader("Content-Type", "application/x-www-form-urlencoded");

		post.setEntity(new UrlEncodedFormEntity(postParams));

		HttpResponse response = client.execute(post);

		int responseCode = response.getStatusLine().getStatusCode();

		System.out.println("\nSending 'POST' request to URL : " + url);
		System.out.println("Post parameters : " + postParams);
		System.out.println("Response Code : " + responseCode);

		BufferedReader rd = new BufferedReader(new InputStreamReader(response
				.getEntity().getContent()));

		StringBuffer result = new StringBuffer();
		String line = "";
		while ((line = rd.readLine()) != null) {
			result.append(line);
		}

		if (responseCode != 200) {
			throw new APIException(result.toString());
		}

		return result.toString();

	}

	/**
	 * Register a new computer.
	 * <p>
	 * This implementation will generate public and private keys for putty. The
	 * public key will be sent to minarca. The computer name is added to the
	 * comments.
	 * 
	 * @param computername
	 * @throws APIException
	 *             if the keys can't be created.
	 */
	public void registerComputer(String computername) throws APIException {
		/*
		 * Generate the keys
		 */
		try {
			// Generate a key pair.
			KeyPair pair = Keygen.generateRSA();

			// Generate a simple id_rsa.pub file.
			Keygen.toPublicIdRsa((RSAPublicKey) pair.getPublic(),
					"imported-openssh-key", "id_rsa.pub");

			// Generate a Putty private key file.
			Keygen.toPrivatePuttyKey(pair, "imported-openssh-key", "mykey.ppk");

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
		
		
		
	}

}
