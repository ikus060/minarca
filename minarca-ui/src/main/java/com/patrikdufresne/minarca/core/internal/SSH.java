package com.patrikdufresne.minarca.core.internal;

import java.io.File;

import org.apache.commons.lang.SystemUtils;

import com.patrikdufresne.minarca.core.APIException;

public abstract class SSH {
	/**
	 * Return the ssh service for this operating system.
	 * 
	 * @return the scheduler service.
	 * @throws UnsupportedOperationException
	 *             if OS is not supported
	 */
	public static SSH getInstance(String remoteHost, String user,
			String password) {
		if (SystemUtils.IS_OS_WINDOWS) {
			return new Plink(remoteHost, user, password);
		} else if (SystemUtils.IS_OS_LINUX) {
			return new Openssh(remoteHost, user, password);
		}
		throw new UnsupportedOperationException(SystemUtils.OS_NAME
				+ " not supported");
	}

	public abstract void sendPublicKey(File publicKey) throws APIException;

}
