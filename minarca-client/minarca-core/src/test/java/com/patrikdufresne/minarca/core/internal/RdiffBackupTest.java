/*
 * Copyright (C) 2020, IKUS Software inc. All rights reserved.
 * IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.core.internal;

import java.io.File;
import java.io.IOException;
import java.util.Arrays;
import java.util.List;

import org.apache.commons.io.FileUtils;
import org.apache.commons.lang3.SystemUtils;
import org.junit.Test;
import org.mockito.Mockito;

import com.patrikdufresne.minarca.core.APIException;

public class RdiffBackupTest {

    @Test
    public void testTestServer() throws IOException, APIException, InterruptedException {
        File hostFile = File.createTempFile("minarcatest", "hostfile");
        FileUtils.write(hostFile, "hostfile");

        File identity = File.createTempFile("minarcatest", "identity");
        FileUtils.write(hostFile, "identity");

        // Mock some part of rdiff backup
        RdiffBackup rdiffbackup = Mockito.spy(new RdiffBackup("example.com:2222", hostFile, identity));
        Mockito.doNothing().when(rdiffbackup).execute(Mockito.anyList(), Mockito.any(File.class));
        Mockito.doReturn(new File("./rdiff-backup")).when(rdiffbackup).getRdiffbackupLocation();
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
                            + "' %s reponame",
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
                            + "' %s reponame",
                    "--test-server",
                    "minarca@example.com::reponame");
        }
        Mockito.verify(rdiffbackup).execute(Mockito.eq(expectedArgs), Mockito.any(File.class));

    }

}
