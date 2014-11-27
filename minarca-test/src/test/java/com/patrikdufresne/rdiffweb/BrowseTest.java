package com.patrikdufresne.rdiffweb;

import static org.junit.Assert.*;

import java.io.IOException;
import java.util.HashSet;
import java.util.Set;

import org.apache.http.client.ClientProtocolException;
import org.junit.Ignore;
import org.junit.Test;

public class BrowseTest extends AbstractRdiffwebTest {

	private String browse(String repo, String path)
			throws ClientProtocolException, IOException {
		return browse(repo, path, false);
	}

	private String browse(String repo, String path, boolean restore)
			throws ClientProtocolException, IOException {
		return get("/browse/" + repo + "/" + path
				+ (restore ? "?restore=T" : ""));
	}

	@Test
	public void testBrowse_Locations() throws ClientProtocolException,
			IOException {
		String data = get("/");
		assertContains(REPO_NAME, data);
	}

	/**
	 * Check a simple browse page.
	 * 
	 * @throws ClientProtocolException
	 * @throws IOException
	 */
	@Test
	public void testBrowse_Root() throws ClientProtocolException, IOException {

		String data = browse(REPO_NAME, "");

		// Fichier @ <root>
		assertContains("Fichier @ &lt;root&gt;", data);
		assertContains(REPO_NAME + "/Fichier%20%40%20%3Croot%3E/?date=", data);

		// Répertoire (@vec) {càraçt#èrë} $épêcial
		assertContains("Répertoire (@vec) {càraçt#èrë} $épêcial", data);
		assertContains(
				REPO_NAME
						+ "/R%C3%A9pertoire%20%28%40vec%29%20%7Bc%C3%A0ra%C3%A7t%23%C3%A8r%C3%AB%7D%20%24%C3%A9p%C3%AAcial/",
				data);

		// test\test
		assertContains("test\\test", data);
		assertContains(REPO_NAME + "/test%5Ctest/", data);

		// <F!chïer> (@vec) {càraçt#èrë} $épêcial
		assertTrue(data
				.contains("&lt;F!chïer&gt; (@vec) {càraçt#èrë} $épêcial"));
		assertTrue(data
				.contains(REPO_NAME
						+ "/%3CF%21ch%C3%AFer%3E%20%28%40vec%29%20%7Bc%C3%A0ra%C3%A7t%23%C3%A8r%C3%AB%7D%20%24%C3%A9p%C3%AAcial/?date="));

		// Répertoire Existant
		assertContains("Répertoire Existant", data);
		assertContains(REPO_NAME + "/R%C3%A9pertoire%20Existant/", data);

		// Répertoire Supprimé
		assertContains("Répertoire Supprimé", data);
		assertContains(REPO_NAME + "/R%C3%A9pertoire%20Supprim%C3%A9/", data);

		// Quoted folder
		assertContains("Char Z to quote", data);
		assertContains(REPO_NAME + "/Char%20%3B090%20to%20quote", data);

		// Invalid encoding
		assertContains("Fichier avec non asci char �velyne M�re.txt", data);
		assertTrue(data
				.contains(REPO_NAME
						+ "/Fichier%20avec%20non%20asci%20char%20%C9velyne%20M%E8re.txt"));

		// Make sure "rdiff-backup-data" is not listed
		assertTrue(!data.contains("rdiff-backup-data"));

		/*
		 * Check restore
		 */
		data = browse(REPO_NAME, "", true);
		assertContains("Download", data);
		assertContains("2014-11-05 16:05", data);
		assertContains("/restore/" + REPO_NAME + "/?date=1415221507", data);

	}

	@Test
	public void testBrowse_SubDirectoryDeleted()
			throws ClientProtocolException, IOException {

		String data = browse(REPO_NAME, "Répertoire%20Supprimé/");
		assertContains("Untitled Empty Text File", data);
		assertContains("Untitled Empty Text File 2", data);
		assertContains("Untitled Empty Text File 3", data);

		// Also check if the filesize are properly retrieve.
		assertContains("21 Bytes", data);
		assertContains("14 Bytes", data);
		assertContains("0 Bytes", data);

		// Also check dates
		assertContains("data-value=\"1414871475\"", data);

		/*
		 * Check restore
		 */
		data = browse(REPO_NAME, "Répertoire%20Supprimé/", true);
		assertContains("Download", data);
		assertContains("ZIP", data);
		assertContains("TAR.GZ", data);
		assertContains("2014-11-01 15:51", data);
		assertContains("/restore/" + REPO_NAME
				+ "/R%C3%A9pertoire%20Supprim%C3%A9/?date=1414871475", data);

	}

	@Test
	public void testBrowse_SubDirectoryExists() throws ClientProtocolException,
			IOException {

		String data = browse(REPO_NAME, "R%C3%A9pertoire%20Existant/");
		assertContains("Fichier supprimé", data);
		assertContains("Untitled Empty Text File", data);
		assertContains("Untitled Empty Text File 2", data);

	}

	@Test
	public void testBrowse_SubDirectoryWithSpecialChars()
			throws ClientProtocolException, IOException {

		String data = browse(
				REPO_NAME,
				"R%C3%A9pertoire%20%28%40vec%29%20%7Bc%C3%A0ra%C3%A7t%23%C3%A8r%C3%AB%7D%20%24%C3%A9p%C3%AAcial/");
		assertContains("Untitled Testcase.doc", data);

		/*
		 * Check restore
		 */
		data = browse(
				REPO_NAME,
				"R%C3%A9pertoire%20%28%40vec%29%20%7Bc%C3%A0ra%C3%A7t%23%C3%A8r%C3%AB%7D%20%24%C3%A9p%C3%AAcial/",
				true);
		assertContains("Download", data);
		assertContains("ZIP", data);
		assertContains("TAR.GZ", data);
		assertContains("2014-11-05 16:05", data);

	}

	@Test
	public void testBrowse_QuotedPath() throws ClientProtocolException,
			IOException {

		// Char ;090 to quote
		// Char Z to quote
		String data = browse(REPO_NAME, "Char%20%3B090%20to%20quote/");

		// browser location
		assertContains("Char Z to quote", data);

		// Content of the folder
		assertContains("Untitled Testcase.doc", data);
		assertContains("Data", data);
		// Check size
		assertContains("21 Bytes", data);
		assertContains("14.8 kB", data);

	}

	/**
	 * Check accessing an invalid repo
	 * 
	 * @throws ClientProtocolException
	 * @throws IOException
	 */
	@Test
	public void testBrowse_InvalidRepo() throws ClientProtocolException,
			IOException {
		try {
			browse("/invalide", "");
			fail("shoudl fail");
		} catch (ApplicationException e) {
			assertContains("Access is denied.", e.getMessage());
		}
		try {
			browse("invalide", "");
			fail("shoudl fail");
		} catch (ApplicationException e) {
			assertContains("Access is denied.", e.getMessage());
		}
	}

	/**
	 * Check accessing an invalid repo
	 * 
	 * @throws ClientProtocolException
	 * @throws IOException
	 */
	@Test
	public void testBrowse_InvalidPath() throws ClientProtocolException,
			IOException {
		try {
			browse(REPO_NAME, "invalid");
			fail("shoudl fail");
		} catch (ApplicationException e) {
			assertContains("The backup location does not exist.",
					e.getMessage());
		}
	}

	/**
	 * Trying to browse "rdiff-backup-data" should fail. Otherwise it's a
	 * security risk.
	 * 
	 * @throws ClientProtocolException
	 * @throws IOException
	 */
	@Test
	public void testBrowse_WithRdiffBackupData()
			throws ClientProtocolException, IOException {

		try {
			browse(REPO_NAME, "rdiff-backup-data");
			fail("should fail");
		} catch (ApplicationException e) {
			assertContains("The backup location does not exist.",
					e.getMessage());
		}

	}

}
