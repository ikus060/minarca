package com.patrikdufresne.rdiffweb;

import static org.junit.Assert.*;

import java.io.IOException;

import org.apache.http.client.ClientProtocolException;
import org.junit.Test;

public class RestoreTest extends AbstractRdiffwebTest {

	public String restore(String repo, String path, String date, Boolean usetar)
			throws ClientProtocolException, IOException {
		return get("/restore/" + repo + "/" + path + "?date=" + date
				+ (usetar ? "&usetar=T" : ""));
	}

	@Test
	public void testRestore_BrokenEncoding() throws ClientProtocolException,
			IOException {
		// restore/?repo=/testcases&path=Fichier%20avec%20non%20asci%20char%20%C9velyne%20M%E8re.txt&date=1415029607
		String data = restore(REPO_NAME,
				"Fichier%20avec%20non%20asci%20char%20%C9velyne%20M%E8re.txt/",
				"1415047607", true);
		assertEquals("Centers the value", data);

		// With subdirectory
		// restore/?repo=/testcases&path=DIR%EF%BF%BD/Data&date=1415059497
		String data2 = restore(REPO_NAME, "DIR%EF%BF%BD/Data/", "1415059497",
				true);
		assertEquals("My Data !", data2);
	}

	/**
	 * Check a simple browse page.
	 * 
	 * @throws ClientProtocolException
	 * @throws IOException
	 */
	@Test
	public void testRestore_File() throws ClientProtocolException, IOException {

		// restore/?repo=/testcases&path=Fichier%20%40%20%3Croot%3E&date=1414921853
		String data = restore(REPO_NAME, "Fichier%20%40%20%3Croot%3E/",
				"1414921853", true);

		assertContains("Ajout d'info", data);

	}

	@Test
	public void testRestore_FileFromQuotedPath()
			throws ClientProtocolException, IOException {

		// restore/?repo=/testcases&path=Char%20%3B090%20to%20quote/Data&date=1414921853
		String data = restore(REPO_NAME, "Char%20%3B090%20to%20quote/Data/",
				"1414921853", true);
		assertEquals("Bring me some Data !", data);

	}

	@Test
	public void testRestore_Root() throws ClientProtocolException, IOException {

		String data = restore(REPO_NAME, "", "1414871387", true);
		// Can't check the data, but we can check the lenght of the data.
		assertEquals(277, data.length());

	}

	@Test
	public void testRestore_Subdirectory() throws ClientProtocolException,
			IOException {

		// /restore/?repo=/testcases&path=R%C3%A9pertoire%20Existant&date=1414871475
		String data = restore(REPO_NAME, "R%C3%A9pertoire%20Existant/",
				"1414871475", true);
		// Can't check the data, but we can check the lenght of the data.
		assertEquals(223, data.length());

	}

	@Test
	public void testRestore_SubdirectoryDeleted()
			throws ClientProtocolException, IOException {

		// /restore/?repo=/testcases&path=R%C3%A9pertoire%20Supprim%C3%A9&date=1414871475
		String data = restore(REPO_NAME, "R%C3%A9pertoire%20Supprim%C3%A9/",
				"1414871475", true);
		// Can't check the data, but we can check the lenght of the data.
		assertEquals(229, data.length());

	}

	@Test
	public void testRestore_WithRevisions() throws ClientProtocolException,
			IOException {
		assertEquals("Version1",
				restore(REPO_NAME, "Revisions/Data", "1415221470", true));
		assertEquals("Version2",
				restore(REPO_NAME, "Revisions/Data", "1415221495", true));
		assertEquals("Version3",
				restore(REPO_NAME, "Revisions/Data", "1415221507", true));
	}

}
