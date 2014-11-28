/*
 * Copyright (c) 2014, Patrik Dufresne Service Logiciel. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.rdiffweb;

import java.io.IOException;

import org.apache.http.client.ClientProtocolException;
import org.junit.Test;

public class HistoryTest extends AbstractRdiffwebTest {

	public String history(String repo) throws ClientProtocolException,
			IOException {
		return get("/history/" + repo);
	}

	/**
	 * Check a simple browse page.
	 * 
	 * @throws ClientProtocolException
	 * @throws IOException
	 */
	@Test
	public void testHistory_File() throws ClientProtocolException, IOException {

		// http://rdiffweb.patrikdufresne.com/restore/?repo=/testcases&path=/Fichier+%40+%3Croot%3E&date=2014-11-01T18%3A07%3A19-04%3A00
		String data = history(REPO_NAME);

		assertContains("2014-11-01 20:51:18", data);
		assertContains("2014-11-01 20:18:11", data);
		assertContains("2014-11-01 20:12:45", data);
		assertContains("2014-11-01 18:07:19", data);
		assertContains("2014-11-01 16:30:50", data);
		assertContains("2014-11-01 16:30:22", data);
		assertContains("2014-11-01 15:51:29", data);
		assertContains("2014-11-01 15:51:15", data);
		assertContains("2014-11-01 15:50:48", data);
		assertContains("2014-11-01 15:50:26", data);
		assertContains("2014-11-01 15:49:47", data);

	}

}
