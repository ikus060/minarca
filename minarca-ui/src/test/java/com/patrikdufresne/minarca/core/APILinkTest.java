package com.patrikdufresne.minarca.core;

import java.io.IOException;
import java.util.Arrays;
import java.util.Date;

import org.junit.Before;
import org.junit.Ignore;
import org.junit.Test;
import org.mockito.Mockito;

import com.patrikdufresne.minarca.core.APIException.InitialBackupFailedException;
import com.patrikdufresne.minarca.core.APIException.InitialBackupHasNotRunException;
import com.patrikdufresne.minarca.core.APIException.InitialBackupRunningException;
import com.patrikdufresne.minarca.core.APIException.LinkComputerException;
import com.patrikdufresne.minarca.core.APIException.RepositoryNameAlreadyInUseException;
import com.patrikdufresne.rdiffweb.core.Client;
import com.patrikdufresne.rdiffweb.core.Repository;

public class APILinkTest {

    private API api;
    private Client client;
    private Config config;

    @Before
    public void setUp() throws APIException, InterruptedException {
        this.client = Mockito.mock(Client.class);
        this.api = Mockito.spy(API.instance());
        this.config = Mockito.spy(new Config());
        Mockito.doReturn(this.config).when(this.api).config();
        Mockito.doNothing().when(this.api).backup(true, true);
        Mockito.doNothing().when(this.config).setSchedule(Mockito.any(Schedule.class));
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
        Repository r = Mockito.mock(Repository.class);
        Mockito.when(this.config.getLastResultDate()).thenReturn(null).thenReturn(new Date());
        Mockito.when(this.config.getLastResult()).thenReturn(LastResult.SUCCESS);
        Mockito.when(this.client.getRepositoryInfo("computername")).thenReturn(null).thenReturn(Arrays.asList(r));

        // Try to link.
        this.api.link("computername", this.client, false);

        // check if SSH key was sent
        Mockito.verify(this.client).addSSHKey(Mockito.eq("computername"), Mockito.anyString());
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
        Mockito.when(this.client.getRepositoryInfo("computername")).thenReturn(null);
        Mockito.when(this.config.getLastResultDate()).thenReturn(null);
        Mockito.when(this.config.getLastResult()).thenReturn(LastResult.HAS_NOT_RUN);
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
        Mockito.when(this.client.getRepositoryInfo("computername")).thenReturn(null);
        Mockito.when(this.config.getLastResultDate()).thenReturn(null);
        Mockito.when(this.config.getLastResult()).thenReturn(LastResult.SUCCESS);
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
        Mockito.when(this.client.getRepositoryInfo("computername")).thenThrow(new IOException());

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
        Repository r = Mockito.mock(Repository.class);
        Mockito.when(this.client.getRepositoryInfo("computername")).thenReturn(Arrays.asList(r));
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
        Repository r = Mockito.mock(Repository.class);
        Mockito.when(this.client.getRepositoryInfo("computername")).thenReturn(Arrays.asList(r));
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
        Repository r = Mockito.mock(Repository.class);
        Mockito.when(this.client.getRepositoryInfo("computername")).thenReturn(Arrays.asList(r));
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
        Repository r = Mockito.mock(Repository.class);
        Mockito.when(this.config.getLastResultDate()).thenReturn(null).thenReturn(new Date());
        Mockito.when(this.config.getLastResult()).thenReturn(LastResult.RUNNING);
        Mockito.when(this.client.getRepositoryInfo("computername")).thenReturn(null).thenReturn(Arrays.asList(r));
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
        Mockito.when(this.config.getLastResultDate()).thenReturn(null).thenReturn(new Date());
        Mockito.when(this.config.getLastResult()).thenReturn(LastResult.RUNNING);
        Mockito.when(this.client.getRepositoryInfo("computername")).thenReturn(null);
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
        Mockito.when(this.client.getRepositoryInfo("computername")).thenReturn(null);
        Mockito.when(this.config.getLastResultDate()).thenReturn(null).thenReturn(new Date());
        Mockito.when(this.config.getLastResult()).thenReturn(null).thenReturn(LastResult.FAILURE);
        Mockito.doNothing().when(this.api).backup(true, true);

        // Try to link.
        this.api.link("computername", this.client, false);
    }

}
