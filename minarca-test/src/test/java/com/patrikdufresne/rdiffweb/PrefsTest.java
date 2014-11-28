/*
 * Copyright (c) 2014, Patrik Dufresne Service Logiciel. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.rdiffweb;

import static org.junit.Assert.fail;

import java.io.IOException;
import java.util.HashMap;
import java.util.Map;

import org.apache.http.client.ClientProtocolException;
import org.junit.Test;

public class PrefsTest extends AbstractRdiffwebTest {

	private static final String PREFS = "/prefs/";

	private String setPassword(String current, String newPassword,
			String confirm) throws ClientProtocolException, IOException {
		Map<String, String> data = new HashMap<String, String>();
		data.put("action", "set_password");
		data.put("current", current);
		data.put("new", newPassword);
		data.put("confirm", confirm);
		return post(PREFS, data);
	}

	@Test
	public void testChangePassword() throws ClientProtocolException,
			IOException {

		String data = setPassword(PASSWORD, "newpass", "newpass");
		assertContains("Password updated successfully.", data);

		String data2 = setPassword("newpass", PASSWORD, PASSWORD);
		assertContains("Password updated successfully.", data2);

	}

	@Test
	public void testChangePassword_WithWrongConfirmation()
			throws ClientProtocolException, IOException {

		try {
			setPassword("oups", "t", "a");
			fail("should fail");
		} catch (ApplicationException e) {
			assertContains("The passwords do not match.", e.getMessage());
		}
	}

	@Test
	public void testChangePassword_WithWrongPassword()
			throws ClientProtocolException, IOException {

		try {
			setPassword("oups", "t", "t");
			fail("should fail");
		} catch (ApplicationException e) {
			assertContains("Invalid credentials", e.getMessage());
		}

	}

	@Test
	public void testUpdateRepos() throws ClientProtocolException, IOException {

		// Update
		String data = updateRepos();
		assertContains("Successfully updated backup locations.", data);

	}

	private String updateRepos() throws ClientProtocolException, IOException {

		Map<String, String> data = new HashMap<String, String>();
		data.put("action", "update_repos");
		return post(PREFS, data);

	}
}
