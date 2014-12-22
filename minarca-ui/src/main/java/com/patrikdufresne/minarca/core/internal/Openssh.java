/*
 * Copyright (c) 2014, Patrik Dufresne Service Logiciel. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.core.internal;

import java.io.File;

import org.jsoup.helper.Validate;

import com.patrikdufresne.minarca.core.APIException;

public class Openssh extends SSH {

    private String password;
    private String remotehost;
    private String username;

    public Openssh(String remotehost, String username, String password) {
        Validate.notNull(this.remotehost = remotehost);
        Validate.notNull(this.username = username);
        Validate.notNull(this.password = password);
    }

    @Override
    public void addKnownHosts() throws APIException {
        // TODO Auto-generated method stub
    }

    @Override
    public void createTextFile(String path, String data) throws APIException {
        // TODO Auto-generated method stub

    }

    @Override
    public void sendPublicKey(File publicKey) throws APIException {
        // TODO Use ssh-copy-id
    }

}
