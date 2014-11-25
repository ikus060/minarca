package com.patrikdufresne.minarca.core.internal;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.UnsupportedEncodingException;
import java.net.CookieHandler;
import java.net.CookieManager;
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

import com.patrikdufresne.minarca.core.APIException;
import com.patrikdufresne.minarca.core.Client;

/**
 * This class is used by the {@link Client} to execute HTTP request.
 * <p>
 * This class hide all the complexity related to user session, authentication
 * and page validation. This class is not indented to be used directly. User
 * should use the {@link Client} interface.
 * 
 * @author ikus060
 *
 */
public class InternalHttpClient {
	/**
	 * The logger
	 */
	private static final transient Logger LOGGER = LoggerFactory
			.getLogger(InternalHttpClient.class);

	/**
	 * Token to look for to distinct login page.
	 */
	private static final String LOGIN_TOKEN = "id=\"form-login\"";

	/**
	 * Login page.
	 */
	private static final String PAGE_LOGIN = "/login/";

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
	/**
	 * The password for login.
	 */
	private String pass;
	/**
	 * The username.
	 */
	private String user;
	private final String USER_AGENT = "Mozilla/5.0";

	/**
	 * Create a new internal HTTP client.
	 * 
	 * @param url
	 *            the base URL
	 * @param user
	 *            the username
	 * @param pass
	 *            the password
	 */
	public InternalHttpClient(String url, String user, String pass) {
		Validate.notNull(this.baseurl = url);
		Validate.notNull(this.user = user);
		Validate.notNull(this.pass = pass);
	}

	/**
	 * Create a named value pair for login form.
	 */
	private List<NameValuePair> createLoginParams()
			throws UnsupportedEncodingException {
		List<NameValuePair> paramList = new ArrayList<NameValuePair>();
		paramList.add(new BasicNameValuePair("login", this.user));
		paramList.add(new BasicNameValuePair("password", this.pass));
		return paramList;
	}

	/**
	 * Used to query a web page.
	 * 
	 * @throws APIException
	 */
	public String get(String url) throws APIException {
		String page;
		try {
			page = httpGet(baseurl + url);
			if (page.contains(LOGIN_TOKEN)) {
				page = httpPost(this.baseurl + PAGE_LOGIN, createLoginParams());
			}
		} catch (IOException e) {
			throw new APIException(e);
		}
		checkPage(page);
		return page;
	}

	private String httpGet(String url) throws ClientProtocolException,
			IOException, APIException {

		HttpGet request = new HttpGet(url);

		request.setHeader("User-Agent", USER_AGENT);
		request.setHeader("Accept",
				"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8");
		request.setHeader("Accept-Language", "en-US,en;q=0.5");

		LOGGER.debug("Sending 'GET' request to URL : {}", url);
		HttpResponse response = client.execute(request);
		int responseCode = response.getStatusLine().getStatusCode();

		LOGGER.debug("Response Code : " + responseCode);

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

	private String httpPost(String url, List<NameValuePair> postParams)
			throws ClientProtocolException, IOException, APIException {

		HttpPost post = new HttpPost(url);

		// add header
		post.setHeader("User-Agent", USER_AGENT);
		post.setHeader("Accept",
				"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8");
		post.setHeader("Accept-Language", "en-US,en;q=0.5");
		post.setHeader("Cookie", this.cookies);
		post.setHeader("Connection", "keep-alive");
		post.setHeader("Referer", this.baseurl);
		post.setHeader("Content-Type", "application/x-www-form-urlencoded");
		post.setEntity(new UrlEncodedFormEntity(postParams));

		LOGGER.debug("Sending 'POST' request to URL : " + url);
		HttpResponse response = client.execute(post);

		int responseCode = response.getStatusLine().getStatusCode();
		LOGGER.debug("Response Code : " + responseCode);

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
	 * Used to query a webpage.
	 * 
	 * @param url
	 * @param data
	 * @return
	 * @throws ClientProtocolException
	 * @throws IOException
	 * @throws APIException
	 */
	public String post(String url, Map<String, String> data)
			throws ClientProtocolException, IOException, APIException {
		// Build the post data.
		List<NameValuePair> postParams = new ArrayList<NameValuePair>();
		for (Entry<String, String> e : data.entrySet()) {
			postParams.add(new BasicNameValuePair(e.getKey(), e.getValue()));
		}

		String page = httpPost(this.baseurl + url, postParams);
		if (page.contains(LOGIN_TOKEN)) {
			page = httpPost(this.baseurl + PAGE_LOGIN, createLoginParams());
			checkPage(page);
			page = httpPost(this.baseurl + url, postParams);
		}

		checkPage(page);

		return page;
	}

}
