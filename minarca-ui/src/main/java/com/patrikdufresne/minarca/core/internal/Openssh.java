package com.patrikdufresne.minarca.core.internal;

import java.io.File;

import org.jsoup.helper.Validate;

import com.patrikdufresne.minarca.core.APIException;

public class Openssh extends SSH {

	private String remotehost;
	private String username;
	private String password;

	public Openssh(String remotehost, String username, String password) {
		Validate.notNull(this.remotehost = remotehost);
		Validate.notNull(this.username = username);
		Validate.notNull(this.password = password);
	}

	@Override
	public void sendPublicKey(File publicKey) throws APIException {
		// TODO Use ssh-copy-id
	}

}
