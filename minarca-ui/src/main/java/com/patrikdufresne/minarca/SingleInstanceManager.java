package com.patrikdufresne.minarca;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.InetAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.net.UnknownHostException;

import org.jsoup.helper.Validate;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Class responsible to detect if a single instance of application is running.
 * 
 * @author Patrik Dufresne
 * 
 */
public class SingleInstanceManager {

    /**
     * Class implementing this interface will be notify when a new instance of the same application is started.
     * 
     * @author Patrik Dufresne
     * 
     */
    public static interface SingleInstanceListener {
        /**
         * Called when a difference instance of the same application is started.
         */
        public void newInstanceCreated();

        /**
         * Called when the running instance should be stopped.
         */
        public void stopInstance();
    }

    static final transient Logger LOGGER = LoggerFactory.getLogger(SingleInstanceManager.class);

    /**
     * Key to identify new instance.
     */
    public static final String SHARED_KEY_NEW_INSTANCE = "$$NewInstance$$";
    /**
     * Key to stop instance.
     */
    public static final String SHARED_KEY_STOP_INSTANCE = "$$StopInstance$$";

    /**
     * Listener to be notify when a new instance is started.
     */
    private SingleInstanceListener listener;

    /**
     * The port to listen on.
     */
    private int port;

    private ServerSocket socket;

    private Thread thread;

    /**
     * Create a new instance of this class.
     * 
     * @param port
     *            the port to be used to verify the uniqueness of the application.
     */
    public SingleInstanceManager(int port) {
        this(port, null);
    }

    /**
     * Create a new instance of this class.
     * 
     * @param port
     *            the port to be used to verify the uniqueness of the application.
     * @param listener
     *            the application listener to be notify when another application is started.
     */
    public SingleInstanceManager(int port, SingleInstanceListener listener) {
        this.port = port;
        this.listener = listener;
    }

    /**
     * Registers this instance of the application.
     * 
     * @return true if first instance, false if not.
     */
    private boolean begin(String sharedkey) {
        // Try to open network socket.
        // If success, listen to socket for new instance message, return true
        try {
            this.socket = new ServerSocket(this.port, 10, InetAddress.getLoopbackAddress());
            LOGGER.debug("listening for application instances on port {}", this.port);
            this.thread = new Thread("single-instance-listener") {
                public void run() {
                    boolean socketClosed = false;
                    while (!socketClosed) {
                        if (socket.isClosed()) {
                            socketClosed = true;
                        } else {
                            try {
                                Socket client = socket.accept();
                                BufferedReader in = new BufferedReader(new InputStreamReader(client.getInputStream()));
                                String message = in.readLine();
                                if (SHARED_KEY_NEW_INSTANCE.equals(message)) {
                                    LOGGER.debug("new application instance found");
                                    fireNewInstance();
                                } else if (SHARED_KEY_STOP_INSTANCE.equals(message)) {
                                    LOGGER.debug("request to stop instance");
                                    fireStopInstance();
                                }
                                in.close();
                                client.close();
                            } catch (IOException e) {
                                socketClosed = true;
                            }
                        }
                    }
                }
            };
            thread.start();
        } catch (UnknownHostException e) {
            // If an unknown network error happen, let the application run.
            LOGGER.error(e.getMessage(), e);
            return true;
        } catch (IOException e) {
            // If unable to open, connect to existing and send new instance message, return false
            LOGGER.debug("port {} is already taken, notifying first instance", this.port);
            try {
                Socket clientSocket = new Socket(InetAddress.getLoopbackAddress(), this.port);
                OutputStream out = clientSocket.getOutputStream();
                out.write(sharedkey.getBytes());
                out.write('\n');
                out.close();
                clientSocket.close();
                LOGGER.debug("successfully notified first instance");
                return false;
            } catch (UnknownHostException e1) {
                LOGGER.error(e.getMessage(), e);
                return true;
            } catch (IOException e1) {
                LOGGER.error("error connecting to local port for single instance notification");
                LOGGER.error(e1.getMessage(), e1);
                return true;
            }

        }
        return true;
    }

    /**
     * Clean-up ressources.
     */
    private void end() {
        if (this.socket != null) {
            try {
                this.socket.close();
            } catch (IOException e) {
                LOGGER.warn("fail to clsoe socket", e);
            }
            this.socket = null;
        }
        if (this.thread != null) {
            this.thread.interrupt();
            this.thread = null;
        }
    }

    /**
     * Used to notify other instance.
     */
    private void fireNewInstance() {
        if (listener != null) {
            listener.newInstanceCreated();
        }
    }

    /**
     * Used to notify instance to be stop.
     */
    private void fireStopInstance() {
        if (listener != null) {
            listener.stopInstance();
        }
    }

    /**
     * Execute this runnable.
     * 
     * @param runnable
     *            the runnable to be executed if first instance.
     * @return True if the runnable was run.
     */
    public boolean run(Runnable runnable) {
        Validate.notNull(runnable);

        // Acquired socket lock.
        if (!begin(SHARED_KEY_NEW_INSTANCE)) {
            return false;
        }

        // Run the runnable.
        try {
            runnable.run();
        } finally {
            end();
        }
        return true;
    }

    /**
     * Define the application listener.
     * 
     * @param listener
     *            the listener.
     */
    public void setApplicationInstanceListener(SingleInstanceListener listener) {
        this.listener = listener;
    }

    /**
     * Send a stop signal to the previously running application.
     * 
     * @return True if the signal was sent.
     */
    public boolean stop() {
        // Try to acquire socket. If not working, we need to send stop signal.
        if (!begin(SHARED_KEY_STOP_INSTANCE)) {
            return true;
        }
        end();
        return false;
    }

}
