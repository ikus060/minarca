package com.patrikdufresne.rdiffweb;

import static org.junit.Assert.*;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.UnsupportedEncodingException;
import java.net.CookieHandler;
import java.net.CookieManager;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Hashtable;
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
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;

public class AbstractRdiffwebTest {

	private static String BASE_URL = "http://rdiffweb.patrikdufresne.com";

	private static final String LOGIN = "/login/";

	protected static final String USERNAME = "rtest";

	protected static final String PASSWORD = "rtest";

	public static final String REPO_NAME = "testcases";

	protected static final String ADMIN_USERS = "/admin/users/";

	static {
		CookieHandler.setDefault(new CookieManager());
	}

	public static void assertContains(String expected, String data) {
		if (!data.contains(expected)) {
			fail(data + " not found in:" + data);
		}
	}

	public static void assertNotContains(String expected, String data) {
		if (data.contains(expected)) {
			fail(data + " not found in given string");
		}
	}

	private HttpClient client = new DefaultHttpClient();

	private String cookies;

	private final String USER_AGENT = "Mozilla/5.0";

	/**
	 * Check if the page return any error.
	 */
	private static void checkPage(String page) {
		// Check error

		Document doc = Jsoup.parse(page);
		Elements elements = doc.getElementsByAttributeValueContaining("class",
				"alert-danger");
		if (elements.size() > 0) {
			throw new ApplicationException(elements.get(0).html());
		}
		if (page.contains("<title>Error</title>")) {
			throw new ApplicationException("unknown!?");
		}
		if (page.contains("Invalid username or password.")) {
			throw new ApplicationException("Invalid username or password.");
		}
	}

	public String get(String url) throws ClientProtocolException, IOException {

		String page = getPageContent(BASE_URL + url);
		if (page.contains("<title>Login")) {
			List<NameValuePair> postParams = getLoginFormParams(page, USERNAME,
					PASSWORD);
			page = sendPost(BASE_URL + LOGIN, postParams);
		}

		checkPage(page);

		return page;
	}

	private String getCookies() {
		return cookies;
	}

	private List<NameValuePair> getFormParams(String html, String formid,
			Map<String, String> replacefields)
			throws UnsupportedEncodingException {

		System.out.println("Extracting form's data...");

		Document doc = Jsoup.parse(html);

		// Google form id
		Elements inputElements;
		if (formid != null) {
			Element loginform = doc.getElementById(formid);
			inputElements = loginform.getElementsByTag("input");
		} else {
			inputElements = doc.getElementsByTag("input");
		}

		List<NameValuePair> paramList = new ArrayList<NameValuePair>();

		for (Element inputElement : inputElements) {
			String key = inputElement.attr("name");
			String value = inputElement.attr("value");

			if (replacefields.containsKey(key)) {
				value = replacefields.get(key);
			}

			paramList.add(new BasicNameValuePair(key, value));

		}

		return paramList;
	}

	private List<NameValuePair> getLoginFormParams(String html,
			String username, String password)
			throws UnsupportedEncodingException {
		Map<String, String> table = new Hashtable<String, String>();
		table.put("login", username);
		table.put("password", password);
		return getFormParams(html, null, table);
	}

	private String getPageContent(String url) throws ClientProtocolException,
			IOException {

		HttpGet request = new HttpGet(url);

		request.setHeader("User-Agent", USER_AGENT);
		request.setHeader("Accept",
				"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8");
		request.setHeader("Accept-Language", "en-US,en;q=0.5");

		HttpResponse response = client.execute(request);
		int responseCode = response.getStatusLine().getStatusCode();

		System.out.println("\nSending 'GET' request to URL : " + url);
		System.out.println("Response Code : " + responseCode);

		BufferedReader rd = new BufferedReader(new InputStreamReader(response
				.getEntity().getContent()));

		StringBuffer result = new StringBuffer();
		String line = "";
		while ((line = rd.readLine()) != null) {
			result.append(line);
		}

		// set cookies
		setCookies(response.getFirstHeader("Set-Cookie") == null ? ""
				: response.getFirstHeader("Set-Cookie").toString());

		if (responseCode != 200) {
			throw new InternalException(result.toString());
		}

		return result.toString();

	}

	public String post(String url, Map<String, String> data)
			throws ClientProtocolException, IOException {
		// Build the post data.
		List<NameValuePair> postParams = new ArrayList<NameValuePair>();
		for (Entry<String, String> e : data.entrySet()) {
			postParams.add(new BasicNameValuePair(e.getKey(), e.getValue()));
		}

		String page = sendPost(BASE_URL + url, postParams);
		if (page.contains("<title>Login")) {
			List<NameValuePair> loginPostParams = getLoginFormParams(page,
					USERNAME, PASSWORD);
			page = sendPost(BASE_URL + LOGIN, loginPostParams);
			checkPage(page);
			page = sendPost(BASE_URL + url, postParams);
		}

		checkPage(page);

		return page;
	}

	private String sendPost(String url, List<NameValuePair> postParams)
			throws ClientProtocolException, IOException {

		HttpPost post = new HttpPost(url);

		// add header
		post.setHeader("User-Agent", USER_AGENT);
		post.setHeader("Accept",
				"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8");
		post.setHeader("Accept-Language", "en-US,en;q=0.5");
		post.setHeader("Cookie", getCookies());
		post.setHeader("Connection", "keep-alive");
		post.setHeader("Referer", BASE_URL);
		post.setHeader("Content-Type", "application/x-www-form-urlencoded");

		post.setEntity(new UrlEncodedFormEntity(postParams, "UTF-8"));

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
			throw new InternalException(result.toString());
		}

		return result.toString();

	}

	private void setCookies(String cookies) {
		this.cookies = cookies;
	}

	protected String editUser(String username, String email, String password,
			String rootDir, Boolean isAdmin) throws ClientProtocolException,
			IOException {
		HashMap<String, String> data = new HashMap<String, String>();
		data.put("action", "edit");
		if (username != null) {
			data.put("username", username);
		}
		if (email != null) {
			data.put("email", email);
		}
		if (password != null) {
			data.put("password", password);
		}
		if (rootDir != null) {
			data.put("user_root", rootDir);
		}
		if (isAdmin != null) {
			data.put("is_admin", isAdmin ? "true" : "");
		}
		return post(ADMIN_USERS, data);
	}
}
