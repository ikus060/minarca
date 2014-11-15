package com.patrikdufresne.rdiffweb;

import static org.junit.Assert.*;

import java.io.IOException;
import java.util.HashMap;

import org.apache.http.client.ClientProtocolException;
import org.junit.After;
import org.junit.Before;
import org.junit.Test;

public class AdminUsersTest extends AbstractRdiffwebTest {

	private String addUser(String username, String email, String password,
			String rootDir, Boolean isAdmin) throws ClientProtocolException,
			IOException {
		HashMap<String, String> data = new HashMap<String, String>();
		data.put("action", "add");
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

	@Before
	public void createUser() throws ClientProtocolException, IOException {
		addUser("test1", "test1@test.com", "test", "/var/backups/", false);
	}

	@After
	public void deleteUser() throws ClientProtocolException, IOException {
		deleteUser("test1");
	}

	private String deleteUser(String username) throws ClientProtocolException,
			IOException {
		HashMap<String, String> data = new HashMap<String, String>();
		data.put("action", "delete");
		if (username != null) {
			data.put("username", username);
		}
		return post(ADMIN_USERS, data);
	}

	@Test
	public void testAddEditDeleteUser() throws ClientProtocolException,
			IOException {

		// Add user to be listed
		String data = addUser("test2", "test2@test.com", "test2",
				"/var/backups/", false);
		assertContains("User added successfully.", data);
		assertContains("test2", data);
		assertContains("test2@test.com", data);

		// Update user
		data = editUser("test2", "chaned@test.com", "new-password", "/tmp/",
				true);
		assertContains("User information modified successfully.", data);
		assertContains("test2", data);
		assertContains("chaned@test.com", data);
		assertContains("/var/backups/", data);

		// Check with filters
		data = get(ADMIN_USERS + "?userfilter=admins");
		assertContains("test2", data);

		// Delete user
		data = deleteUser("test2");
		assertContains("User account removed.", data);
		assertTrue(!data.contains("test2"));

	}

	@Test
	public void testAddEditDeleteUser_WithEncoding()
			throws ClientProtocolException, IOException {

		// Add user to be listed
		String data = addUser("Éric", "éric@test.com", "Éric",
				"/var/backups/", false);
		assertContains("User added successfully.", data);
		assertContains("Éric", data);
		assertContains("éric@test.com", data);

		// Update user
		data = editUser("Éric", "eric.létourno@test.com", "écureuil", "/tmp/",
				true);
		assertContains("User information modified successfully.", data);
		assertContains("Éric", data);
		assertContains("eric.létourno@test.com", data);
		assertContains("/var/backups/", data);

		// Check with filters
		data = get(ADMIN_USERS + "?userfilter=admins");
		assertContains("Éric", data);

		// Delete user
		data = deleteUser("Éric");
		assertContains("User account removed.", data);
		assertTrue(!data.contains("Éric"));

	}

	@Test
	public void testAddUser_WithEmptyUsername() throws ClientProtocolException,
			IOException {
		try {
			addUser("", "test1@test.com", "test1", "/var/backups/", false);
			fail("expected to fail");
		} catch (ApplicationException e) {
			assertContains("The username is invalid.", e.getMessage());
		}
	}

	@Test
	public void testAddUser_WithExistingUsername()
			throws ClientProtocolException, IOException {
		try {
			addUser("test1", "test1@test.com", "test1", "/var/backups/", false);
			fail("expected to fail");
		} catch (ApplicationException e) {
			assertContains("The specified user already exists.", e.getMessage());
		}
	}

	@Test
	public void testAddUser_WithInvalidRootDirectory()
			throws ClientProtocolException, IOException {
		// Add user with invalid path
		String data = addUser("test5", "test1@test.com", "test5",
				"/var/invalid/", false);
		assertContains("User added successfully.", data);

		// Make sure a warning is displayed.
		assertContains(
				"User root directory [/var/invalid/] is not accessible!", data);
	}

	@Test
	public void testDeleteUser_WithNotExistingUsername()
			throws ClientProtocolException, IOException {
		try {
			deleteUser("test3");
			fail("expected to fail");
		} catch (ApplicationException e) {
			assertContains("The user does not exist.", e.getMessage());
		}
	}

	@Test
	public void testEditUser_WithInvalidPath() throws ClientProtocolException,
			IOException {
		String data = editUser("test1", "test1@test.com", "test",
				"/var/invalid/", false);
		assertContains(
				"User root directory [/var/invalid/] is not accessible!", data);
	}

	@Test
	public void testList() throws ClientProtocolException, IOException {

		String data = get(ADMIN_USERS);
		assertContains("Users", data);
		assertContains("User management", data);
		assertContains("Add user", data);

		// Check if "test1" exists
		assertContains("test1", data);
		assertContains("test1@test.com", data);
		assertContains("/var/backups/", data);

	}

	@Test
	public void testUpdateUser_WithNotExistingUsername()
			throws ClientProtocolException, IOException {
		try {
			editUser("test4", "test1@test.com", "test1", "/var/backups/", false);
		} catch (ApplicationException e) {
			assertContains("The user does not exist.", e.getMessage());
		}
	}

	@Test
	public void testUserfilter() throws ClientProtocolException, IOException {

		String data = get(ADMIN_USERS + "?userfilter=admins");
		assertTrue(!data.contains("test1"));

	}

	@Test
	public void testUsersearch() throws ClientProtocolException, IOException {

		String data = get(ADMIN_USERS + "?usersearch=tes");
		assertContains("test1", data);

		data = get(ADMIN_USERS + "?usersearch=coucou");
		assertTrue(!data.contains("test1"));

	}

}
