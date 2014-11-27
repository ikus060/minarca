package com.patrikdufresne.rdiffweb;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

import org.apache.http.NameValuePair;
import org.apache.http.client.ClientProtocolException;
import org.apache.http.message.BasicNameValuePair;
import org.junit.Test;

public class LoginTest extends AbstractRdiffwebTest {

	@Test
	public void testLogin_WithRedirectGet() throws ClientProtocolException,
			IOException {
		// Query the page without login-in
		String page = getPageContent(BASE_URL
				+ "/browse/testcases/DIR%EF%BF%BD/");
		// Should be the login page
		assertContains("<title>Login", page);

		assertContains("value=\"/browse/testcases/DIR%EF%BF%BD/\"", page);
	}

	@Test
	public void testLogin_WithRedirectPost() throws ClientProtocolException,
			IOException {

		List<NameValuePair> params = new ArrayList<NameValuePair>();
		params.add(new BasicNameValuePair("login", "oups"));
		params.add(new BasicNameValuePair("password", "oups"));
		params.add(new BasicNameValuePair("redirect",
				"/browse/testcases/DIR%EF%BF%BD/"));

		String page = sendPost(BASE_URL + LOGIN, params);

		// Should be the login page
		assertContains("<title>Login", page);

		assertContains("value=\"/browse/testcases/DIR%EF%BF%BD/\"", page);

	}

	@Test
	public void testLogin_WithQueryStringRedirectGet()
			throws ClientProtocolException, IOException {

		// Query the page without login-in
		String page = getPageContent(BASE_URL + "/browse/testcases/?restore=T");
		assertContains("<title>Login", page);
		assertContains("value=\"/browse/testcases/?restore=T\"", page);

		// Check with multiple param
		String page2 = getPageContent(BASE_URL
				+ "/restore/testcases/?date=1414871387&usetar=T");
		assertContains("<title>Login", page2);
		assertContains(
				"value=\"/restore/testcases/?date=1414871387&amp;usetar=T\"",
				page2);

	}

	@Test
	public void testLogin_WithRedirection() throws ClientProtocolException,
			IOException {

		List<NameValuePair> params = new ArrayList<NameValuePair>();
		params.add(new BasicNameValuePair("login", USERNAME));
		params.add(new BasicNameValuePair("password", PASSWORD));
		params.add(new BasicNameValuePair("redirect",
				"/restore/testcases/?date=1414871387&usetar=T"));

		String page = sendPost(BASE_URL + LOGIN, params);

	}

	@Test
	public void testLogin_WithEmptyPassword() throws ClientProtocolException,
			IOException {

		List<NameValuePair> params = new ArrayList<NameValuePair>();
		params.add(new BasicNameValuePair("login", USERNAME));
		params.add(new BasicNameValuePair("password", ""));

		String page = sendPost(BASE_URL + LOGIN, params);
		assertContains("Invalid username or password.", page);
	}

}
