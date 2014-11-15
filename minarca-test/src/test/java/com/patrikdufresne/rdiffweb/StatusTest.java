package com.patrikdufresne.rdiffweb;

import static org.junit.Assert.*;

import java.io.IOException;

import org.apache.http.client.ClientProtocolException;
import org.junit.Test;

public class StatusTest extends AbstractRdiffwebTest {

	/**
	 * Check a simple browse page.
	 * 
	 * @throws ClientProtocolException
	 * @throws IOException
	 */
	@Test
	public void testStatus_File() throws ClientProtocolException, IOException {

		// http://rdiffweb.patrikdufresne.com/restore/?repo=/testcases&path=/Fichier+%40+%3Croot%3E&date=2014-11-01T18%3A07%3A19-04%3A00
		String data = get("/status/");

	}

}
