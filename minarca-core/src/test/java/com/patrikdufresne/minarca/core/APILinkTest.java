/*
 * Copyright (C) 2020, IKUS Software inc. All rights reserved.
 * IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.core;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.Collections;
import java.util.Date;
import java.util.List;

import org.apache.commons.io.FileUtils;
import org.junit.AfterClass;
import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.Ignore;
import org.junit.Test;
import org.mockito.Mockito;

import com.patrikdufresne.minarca.core.APIException.InitialBackupFailedException;
import com.patrikdufresne.minarca.core.APIException.InitialBackupHasNotRunException;
import com.patrikdufresne.minarca.core.APIException.InitialBackupRunningException;
import com.patrikdufresne.minarca.core.APIException.LinkComputerException;
import com.patrikdufresne.minarca.core.APIException.RepositoryNameAlreadyInUseException;
import com.patrikdufresne.minarca.core.internal.SchedulerLinux;
import com.patrikdufresne.minarca.core.model.CurrentUser;
import com.patrikdufresne.minarca.core.model.MinarcaInfo;
import com.patrikdufresne.minarca.core.model.Repo;

public class APILinkTest {

    private static Path tmpdir;

    private static List<Repo> defaultRepos(String name) {
        Repo r = new Repo();
        r.name = name;
        return Arrays.asList(r);
    }

    @AfterClass
    static public void deleteConfigPath() throws IOException {
        FileUtils.deleteDirectory(tmpdir.toFile());
    }

    @BeforeClass
    static public void setConfigPath() throws IOException {
        System.out.println("@BeforeClass");
        // Enforce different config path for the test
        tmpdir = Files.createTempDirectory("minarca-link-test");
        System.setProperty("com.patrikdufresne.minarca.configPath", tmpdir.toString());
        System.setProperty("com.patrikdufresne.minarca.dataPath", tmpdir.toString());
    }

    private API api;

    private Client client;

    private final Status FAILURE = new Status(LastResult.FAILURE, new Date(1566989923000l), new Date(1566989923000l));

    private final Status HAS_NOT_RUN = new Status(LastResult.HAS_NOT_RUN, null, null);

    private final Status RUNNING = new Status(LastResult.RUNNING, new Date(1566989923000l), new Date(1566989923000l));

    private final Status SUCCESS = new Status(LastResult.SUCCESS, new Date(1566989923000l), new Date(1566989923000l));

    @Before
    public void setUp() throws APIException, InterruptedException, IOException {

        // Mock the client
        this.client = Mockito.mock(Client.class);
        this.api = Mockito.spy(API.instance());
        this.api.config = Mockito.spy(new Config());
        Mockito.doNothing().when(this.api).backup(true, true);
        Mockito.doNothing().when(this.api.config).setSchedule(Mockito.any(Schedule.class), Mockito.anyBoolean());
        MinarcaInfo minarcaInfo = new MinarcaInfo();
        minarcaInfo.identity = "some ssh key";
        minarcaInfo.remotehost = "remotehost:22";
        Mockito.when(this.client.getMinarcaInfo()).thenReturn(minarcaInfo);
        System.setProperty("minarca.link.timeoutsec", "30");
    }

    /**
     * Check if linking is working as expected.
     * 
     * @throws APIException
     * @throws InterruptedException
     * @throws IOException
     */
    @Test
    public void testLink() throws APIException, InterruptedException, IOException {
        // Mock the client.
        Mockito.when(this.api.status()).thenReturn(HAS_NOT_RUN).thenReturn(SUCCESS);
        CurrentUser first = new CurrentUser();
        first.repos = Collections.emptyList();
        CurrentUser second = new CurrentUser();
        second.repos = defaultRepos("computername/C");
        Mockito.when(this.client.getCurrentUserInfo()).thenReturn(first).thenReturn(second);

        // Try to link.
        this.api.link("computername", this.client, false);

        // check if SSH key was sent
        Mockito.verify(this.client).addSSHKey(Mockito.eq("computername"), Mockito.anyString());
        Mockito.verify(this.client).setRepoEncoding(Mockito.eq("computername/C"), Mockito.anyString());
        Mockito.verify(this.api).backup(true, true);
    }

    /**
     * Check if exception is raised when initial backup failed.
     * 
     * @throws APIException
     * @throws InterruptedException
     * @throws IOException
     */
    @Ignore
    @Test(expected = InitialBackupHasNotRunException.class)
    public void testLink_WithHasNotRun() throws APIException, InterruptedException, IOException {
        // Mock the client.
        CurrentUser first = new CurrentUser();
        first.repos = Collections.emptyList();
        CurrentUser second = new CurrentUser();
        second.repos = defaultRepos("computername");
        Mockito.when(this.client.getCurrentUserInfo()).thenReturn(first);
        Mockito.when(this.api.status()).thenReturn(HAS_NOT_RUN);
        Mockito.doNothing().when(this.api).backup(true, true);

        // Try to link.
        this.api.link("computername", this.client, false);
    }

    /**
     * Check if exception is raised when initial backup failed.
     * 
     * @throws APIException
     * @throws InterruptedException
     * @throws IOException
     */
    @Test(expected = IOException.class)
    public void testLink_WithHttpError() throws APIException, InterruptedException, IOException {
        // Mock the client.
        Mockito.when(this.client.getCurrentUserInfo()).thenThrow(new IOException());

        // Try to link.
        this.api.link("computername", this.client, false);
    }

    /**
     * Check if exception when computer already exists.
     * 
     * @throws APIException
     * @throws InterruptedException
     * @throws IOException
     */
    @Test(expected = RepositoryNameAlreadyInUseException.class)
    public void testLink_WithRepoExists() throws APIException, InterruptedException, IOException {
        // Mock the client.
        CurrentUser first = new CurrentUser();
        first.repos = defaultRepos("computername/C");
        Mockito.when(this.client.getCurrentUserInfo()).thenReturn(first);
        Mockito.doNothing().when(this.api).backup(true, true);

        // Try to link.
        this.api.link("computername", this.client, false);

    }

    /**
     * Check if exception when computer already exists.
     * 
     * @throws APIException
     * @throws InterruptedException
     * @throws IOException
     */
    @Test
    public void testLink_WithRepoExistsForce() throws APIException, InterruptedException, IOException {
        // Mock the client.
        CurrentUser first = new CurrentUser();
        first.repos = defaultRepos("computername/C");
        Mockito.when(this.client.getCurrentUserInfo()).thenReturn(first);
        Mockito.doNothing().when(this.api).backup(true, true);

        // Try to link.
        this.api.link("computername", this.client, true);

        // Make to we are not running a backup.
        Mockito.verify(this.api, Mockito.never()).backup(true, true);
    }

    /**
     * Check if exception is raised when the computer already exists.
     * 
     * @throws APIException
     * @throws InterruptedException
     * @throws IOException
     */
    @Test(expected = RepositoryNameAlreadyInUseException.class)
    public void testLink_WithRepositoryExists() throws APIException, InterruptedException, IOException {
        // Mock the client.
        CurrentUser first = new CurrentUser();
        first.repos = defaultRepos("computername/C");
        Mockito.when(this.client.getCurrentUserInfo()).thenReturn(first);
        Mockito.doNothing().when(this.api).backup(true, true);

        // Try to link.
        API.instance().link("computername", this.client, false);
    }

    /**
     * Check if link is success if running and exists.
     * 
     * @throws APIException
     * @throws InterruptedException
     * @throws IOException
     */
    @Test
    public void testLink_WithRunningExists() throws APIException, InterruptedException, IOException {
        // Mock the client.
        Mockito.when(this.api.status()).thenReturn(HAS_NOT_RUN).thenReturn(RUNNING);
        CurrentUser first = new CurrentUser();
        first.repos = Collections.emptyList();
        CurrentUser second = new CurrentUser();
        second.repos = defaultRepos("computername/C");
        Mockito.when(this.client.getCurrentUserInfo()).thenReturn(first).thenReturn(second);
        Mockito.doNothing().when(this.api).backup(true, true);

        // Try to link.
        this.api.link("computername", this.client, false);
    }

    /**
     * Check if link is exception if running and exists.
     * 
     * @throws APIException
     * @throws InterruptedException
     * @throws IOException
     */
    @Ignore
    @Test(expected = InitialBackupRunningException.class)
    public void testLink_WithRunningNotExists() throws APIException, InterruptedException, IOException {
        // Mock the client.
        Mockito.when(this.api.status()).thenReturn(HAS_NOT_RUN).thenReturn(RUNNING);
        CurrentUser first = new CurrentUser();
        first.repos = Collections.emptyList();
        Mockito.when(this.client.getCurrentUserInfo()).thenReturn(first);
        Mockito.doNothing().when(this.api).backup(true, true);

        // Try to link.
        this.api.link("computername", this.client, false);
    }

    /**
     * Check if exception is raised when initial backup failed.
     * 
     * @throws APIException
     * @throws InterruptedException
     * @throws IOException
     */
    @Ignore
    @Test(expected = InitialBackupFailedException.class)
    public void testLink_WithScheduleFailed() throws APIException, InterruptedException, IOException {
        // Mock the client.
        CurrentUser first = new CurrentUser();
        first.repos = Collections.emptyList();
        Mockito.when(this.client.getCurrentUserInfo()).thenReturn(first);
        Mockito.when(this.api.status()).thenReturn(HAS_NOT_RUN).thenReturn(FAILURE);
        Mockito.doNothing().when(this.api).backup(true, true);

        // Try to link.
        this.api.link("computername", this.client, false);
    }

    /**
     * Check if exception is raised when initial backup success but the repository doesn't exists.
     * 
     * @throws APIException
     * @throws InterruptedException
     * @throws IOException
     */
    @Test(expected = LinkComputerException.class)
    public void testLink_WithSuccessNotExists() throws APIException, InterruptedException, IOException {
        // Mock the client.
        CurrentUser first = new CurrentUser();
        first.repos = Collections.emptyList();
        CurrentUser second = new CurrentUser();
        second.repos = defaultRepos("computername");
        Mockito.when(this.client.getCurrentUserInfo()).thenReturn(first);
        Mockito.when(this.api.status()).thenReturn(SUCCESS);
        Mockito.doNothing().when(this.api).backup(true, true);

        // Try to link.
        this.api.link("computername", this.client, false);
    }

}
