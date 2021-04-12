/*
 * Copyright (C) 2020, IKUS Software inc. All rights reserved.
 * IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.core.internal;

import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

import java.io.File;
import java.io.IOException;
import java.util.Arrays;
import java.util.List;

import org.apache.commons.io.FileUtils;
import org.apache.commons.lang3.SystemUtils;
import org.junit.Before;
import org.junit.Test;
import org.mockito.Mockito;

import com.patrikdufresne.minarca.core.API;
import com.patrikdufresne.minarca.core.APIException;
import com.patrikdufresne.minarca.core.APIException.RdiffBackupMissingException;

public class RdiffBackupTest {

    RdiffBackup rdiffbackup;

    File hostFile;

    File identity;

    @Before
    public void initRdiffBackup() throws IOException, APIException, InterruptedException {
        hostFile = File.createTempFile("minarcatest", "hostfile");
        FileUtils.write(hostFile, "hostfile");

        identity = File.createTempFile("minarcatest", "identity");
        FileUtils.write(hostFile, "identity");

        // Mock some part of rdiff backup
        rdiffbackup = Mockito.spy(new RdiffBackup("example.com:2222", hostFile, identity));
    }

    @Test
    public void testTestServer() throws IOException, APIException, InterruptedException {
        Mockito.doNothing().when(rdiffbackup).execute(Mockito.anyList(), Mockito.any(File.class));
        Mockito.doReturn("userAgentString").when(rdiffbackup).getUserAgent();
        Mockito.doReturn(new File("./rdiff-backup")).when(rdiffbackup).getRdiffBackupLocation();
        Mockito.doReturn(new File("./ssh")).when(rdiffbackup).getSshLocation();

        // Make a call
        rdiffbackup.testServer("reponame");

        // Check results
        List<String> expectedArgs;
        if (SystemUtils.IS_OS_WINDOWS) {
            expectedArgs = Arrays.asList(
                    ".\\rdiff-backup",
                    "-v",
                    "5",
                    "--remote-schema",
                    ".\\ssh -p 2222 -oBatchMode=yes -oPreferredAuthentications=publickey -oUserKnownHostsFile='"
                            + hostFile.toString()
                            + "' -oIdentitiesOnly=yes -i '"
                            + identity.toString()
                            + "' %s 'userAgentString'",
                    "--test-server",
                    "minarca@example.com::reponame");
        } else {
            expectedArgs = Arrays.asList(
                    "./rdiff-backup",
                    "-v",
                    "5",
                    "--remote-schema",
                    "./ssh -p 2222 -oBatchMode=yes -oPreferredAuthentications=publickey -oUserKnownHostsFile='"
                            + hostFile.toString()
                            + "' -oIdentitiesOnly=yes -i '"
                            + identity.toString()
                            + "' %s 'userAgentString'",
                    "--test-server",
                    "minarca@example.com::reponame");
        }
        Mockito.verify(rdiffbackup).execute(Mockito.eq(expectedArgs), Mockito.any(File.class));

    }

    @Test
    public void testGetUserAgentString() throws IOException, APIException, InterruptedException {
        Mockito.doReturn("2.0.5").when(rdiffbackup).getRdiffBackupVersion();
        assertTrue(rdiffbackup.getUserAgent().contains("minarca/" + API.getCurrentVersion()));
        assertTrue(rdiffbackup.getUserAgent().contains(" rdiff-backup/2.0.5 "));
        if (SystemUtils.IS_OS_WINDOWS) {
            assertTrue(rdiffbackup.getUserAgent().contains("Windows"));
        } else {
            assertTrue(rdiffbackup.getUserAgent().contains("Linux"));
        }
    }

    @Test
    public void testGetRdiffBackupVersion() throws RdiffBackupMissingException {
        String version = rdiffbackup.getRdiffBackupVersion();
        assertNotNull(version);
    }

}
