/*
 * Copyright (C) 2015, Patrik Dufresne Service Logiciel inc. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.core.internal;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.io.Reader;
import java.io.Writer;
import java.math.BigInteger;
import java.security.InvalidKeyException;
import java.security.KeyFactory;
import java.security.KeyPair;
import java.security.KeyPairGenerator;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.security.Security;
import java.security.interfaces.RSAPrivateCrtKey;
import java.security.interfaces.RSAPrivateKey;
import java.security.interfaces.RSAPublicKey;
import java.security.spec.InvalidKeySpecException;
import java.security.spec.RSAPublicKeySpec;
import java.util.List;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

import org.apache.commons.codec.binary.Base64;
import org.apache.commons.codec.binary.Hex;
import org.apache.commons.io.IOUtils;
import org.apache.commons.io.output.FileWriterWithEncoding;
import org.apache.commons.lang3.SystemUtils;
import org.apache.commons.lang3.Validate;
import org.bouncycastle.jce.provider.BouncyCastleProvider;
import org.bouncycastle.openssl.PEMWriter;

/**
 * Provide basics to generate public and private key file for OpenSSH and Putty.
 * <p>
 * Current implementation doesn't support passphrase (since I don't need it).
 * 
 * @author Patrik Dufresne
 * 
 */
public class Keygen {
    /**
     * HMAC-SHA-1 algorithm
     */
    private static final String ALGORITHM_HMAC_SHA1 = "HmacSHA1";
    /**
     * RSA algorithm.
     */
    private static final String ALGORITHM_RSA = "RSA";
    /**
     * SHA-1 algorithm
     */
    private static final String ALGORITHM_SHA_1 = "SHA-1";
    /**
     * Bouncy castle algorithm provider.
     */
    private static final BouncyCastleProvider BC;
    /**
     * Newline chars
     */
    private static final String CRLF = "\r\n";
    /**
     * Putty encryption
     */
    private static final String ENCRYPTION = "none";

    /**
     * Default RSA keysize (value: 2048).
     */
    private static final int KEYSIZE = 2048;

    /**
     * Putty Key type
     */
    private static final String TYPE = "ssh-rsa";

    /**
     * UTF-8 charset name.
     */
    private static final String UTF_8 = "utf-8";
    static {
        // Register the provider.
        Security.addProvider(BC = new BouncyCastleProvider());
    }

    /**
     * Count the number of line
     * 
     * @param value
     *            the string to be wrap
     * @param col
     *            number of char on a single line.
     * @return
     */
    private static int countLines(String value, int col) {
        return (value.length() + col - 1) / col;
    }

    /**
     * From Base64 to bytes.
     * 
     * @param base64
     * @return
     */
    private static byte[] decodeBase64(String base64) {
        return Base64.decodeBase64(base64);
    }

    /**
     * From bytes to Base64 string
     * 
     * @param bytes
     * @return
     */
    private static String encodeBase64(byte[] bytes) {
        return new String(Base64.encodeBase64(bytes));
    }

    /**
     * From bytes to Hexadecimal string
     * 
     * @param bytes
     * @return
     */
    private static String encodeHex(byte[] bytes) {
        return new String(Hex.encodeHex(bytes));
    }

    /**
     * Generate a valid private key compatible for putty.
     * 
     * @param rsaPrivateKey
     *            the private key
     * @return encoded version of the privated key
     * @throws IOException
     * @see https://github.com/Yasushi/putty/blob/master/sshpubk.c
     */
    private static byte[] encodePrivateKeyForPutty(RSAPrivateCrtKey rsaPrivateKey) throws IOException {
        ByteArrayOutputStream byteOs = new ByteArrayOutputStream();
        DataOutputStream dos = new DataOutputStream(byteOs);
        // mpint private_exponent
        dos.writeInt(rsaPrivateKey.getPrivateExponent().toByteArray().length);
        dos.write(rsaPrivateKey.getPrivateExponent().toByteArray());
        // mpint p (the larger of the two primes)
        dos.writeInt(rsaPrivateKey.getPrimeP().toByteArray().length);
        dos.write(rsaPrivateKey.getPrimeP().toByteArray());
        // mpint q (the smaller prime)
        dos.writeInt(rsaPrivateKey.getPrimeQ().toByteArray().length);
        dos.write(rsaPrivateKey.getPrimeQ().toByteArray());
        // mpint iqmp (the inverse of q modulo p)
        dos.writeInt(rsaPrivateKey.getCrtCoefficient().toByteArray().length);
        dos.write(rsaPrivateKey.getCrtCoefficient().toByteArray());
        dos.close();
        byteOs.close();
        return byteOs.toByteArray();
    }

    /**
     * Generate a standard ssh2 RSA key (to be used with OpenSSH)
     * 
     * @param rsaPublicKey
     *            the public key
     * @return encoded public key in base 64
     * @throws IOException
     */
    private static byte[] encodePublicKey(RSAPublicKey rsaPublicKey) throws IOException {
        ByteArrayOutputStream byteOs = new ByteArrayOutputStream();
        DataOutputStream dos = new DataOutputStream(byteOs);
        // String "ssh-rsa"
        dos.writeInt("ssh-rsa".getBytes().length);
        dos.write("ssh-rsa".getBytes());
        // mpint exponent
        dos.writeInt(rsaPublicKey.getPublicExponent().toByteArray().length);
        dos.write(rsaPublicKey.getPublicExponent().toByteArray());
        // mpint modulus
        dos.writeInt(rsaPublicKey.getModulus().toByteArray().length);
        dos.write(rsaPublicKey.getModulus().toByteArray());
        dos.close();
        byteOs.close();
        return byteOs.toByteArray();
    }

    public static RSAPublicKey fromPublicIdRsa(File file) throws IOException, InvalidKeySpecException, NoSuchAlgorithmException {
        FileReader reader = new FileReader(file);
        try {
            return fromPublicIdRsa(reader);
        } finally {
            reader.close();
        }
    }

    /**
     * Read a public RSA key.
     * 
     * @param file
     *            the file to be read.
     * @return
     * @throws IOException
     * @throws NoSuchAlgorithmException
     * @throws InvalidKeySpecException
     */
    public static RSAPublicKey fromPublicIdRsa(Reader reader) throws IOException, InvalidKeySpecException, NoSuchAlgorithmException {
        List<String> lines = IOUtils.readLines(reader);
        if (lines.size() > 2) {
            throw new IOException("two many line in file");
        }
        String fields[] = lines.get(0).split("\\s");
        if (!fields[0].equals("ssh-rsa")) {
            throw new IOException("unsupported key: " + fields[1]);
        }
        byte[] bytes = decodeBase64(fields[1]);

        // Read the bytes.
        int length;
        byte[] data;
        DataInputStream in = new DataInputStream(new ByteArrayInputStream(bytes));
        // String "ssh-rsa"
        length = in.readInt();
        data = new byte[length];
        in.read(data);
        String keytype = new String(data);
        if (!keytype.equals("ssh-rsa")) {
            throw new IOException("unsupported key: " + keytype);
        }
        // mpint exponent
        length = in.readInt();
        data = new byte[length];
        in.read(data);
        BigInteger e = new BigInteger(data);
        // mpint modulus
        length = in.readInt();
        data = new byte[length];
        in.read(data);
        BigInteger n = new BigInteger(data);
        // Convert the integers to Java object key,
        final RSAPublicKeySpec rsaPubSpec = new RSAPublicKeySpec(n, e);
        return (RSAPublicKey) KeyFactory.getInstance("RSA").generatePublic(rsaPubSpec);
    }

    /**
     * Generate an RSA key pair (of 1024 bytes).
     * 
     * @return
     * @throws NoSuchAlgorithmException
     */
    public static KeyPair generateRSA() throws NoSuchAlgorithmException {
        return generateRSA(KEYSIZE);
    }

    /**
     * Generate an RSA key pair (of given size).
     * 
     * @return the keypair
     * 
     * @throws NoSuchAlgorithmException
     */
    public static KeyPair generateRSA(int keysize) throws NoSuchAlgorithmException {
        KeyPairGenerator keyGen = KeyPairGenerator.getInstance(ALGORITHM_RSA, BC);
        keyGen.initialize(keysize);
        return keyGen.genKeyPair();
    }

    /**
     * Generate a MD5 finger print for a public key.
     * 
     * @param publicKey
     * 
     * @return the md5 finger print.
     * @throws IOException
     */
    public static String getFingerPrint(RSAPublicKey publicKey) throws NoSuchAlgorithmException, IOException {
        MessageDigest md5 = MessageDigest.getInstance("MD5");
        byte[] bytes = md5.digest(encodePublicKey(publicKey));
        StringBuffer sb = new StringBuffer();
        for (int i = 0; i < bytes.length; ++i) {
            if (sb.length() > 0) {
                sb.append(":");
            }
            sb.append(Integer.toHexString((bytes[i] & 0xFF) | 0x100).substring(1, 3));
        }
        return sb.toString();
    }

    /**
     * Open a file as FileWriter with the given encoding.
     * 
     * @param file
     *            the file
     * @param encoding
     *            the encoding to be used to read the file
     * @return the file writer.
     * @throws IOException
     */
    private static FileWriterWithEncoding openFileWriter(File file, String encoding) throws IOException {
        if (file.exists()) {
            if (file.isDirectory()) {
                throw new IOException("File '" + file + "' exists but is a directory");
            }
            if (!file.canWrite()) {
                // Try to change permission
                file.setWritable(true, true);
            }
            if (!file.canWrite()) {

                throw new IOException("File '" + file + "' cannot be written to");
            }
        } else {
            File parent = file.getParentFile();
            if (parent != null) {
                if (!parent.mkdirs() && !parent.isDirectory()) {
                    throw new IOException("Directory '" + parent + "' could not be created");
                }
            }
        }
        return new FileWriterWithEncoding(file, UTF_8);
    }

    /**
     * Generate a PEM file.
     * 
     * @param privateKey
     *            the private key
     * @param file
     *            where to write the key
     * @throws IOException
     */
    public static void toPrivatePEM(RSAPrivateKey privateKey, File file) throws IOException {
        FileWriterWithEncoding idrsa = openFileWriter(file, UTF_8);
        toPrivatePEM(privateKey, idrsa);
        idrsa.close();
        // Set permissions (otherwise SSH complains about file permissions)
        if (SystemUtils.IS_OS_LINUX) {
            file.setExecutable(false, false);
            file.setReadable(false, false);
            file.setWritable(false, false);
            file.setWritable(true, true);
            file.setReadable(true, true);
        }
    }

    /**
     * Generate a PEM file.
     * 
     * @param privateKey
     *            the private key
     * @param writer
     *            where to write the key
     * @throws IOException
     */
    public static void toPrivatePEM(RSAPrivateKey privateKey, Writer writer) throws IOException {
        PEMWriter pemFormatWriter = new PEMWriter(writer);
        pemFormatWriter.writeObject(privateKey);
        pemFormatWriter.close();
    }

    /**
     * Generate a Putty private key file (ppk).
     * <p>
     * This implementation use default encoding.
     * 
     * @param pair
     *            the key pair
     * @param comment
     *            the comment.
     * @param file
     *            the filename
     * @throws IOException
     * @throws NoSuchAlgorithmException
     * @throws InvalidKeyException
     */
    public static void toPrivatePuttyKey(KeyPair pair, String comment, File file) throws IOException, NoSuchAlgorithmException, InvalidKeyException {
        FileWriterWithEncoding writer = openFileWriter(file, Compat.CHARSET_DEFAULT.name());
        toPrivatePuttyKey(pair, comment, writer);
        writer.close();
        // Set permissions (otherwise SSH complains about file permissions)
        if (SystemUtils.IS_OS_LINUX) {
            file.setExecutable(false, false);
            file.setReadable(false, false);
            file.setWritable(false, false);
            file.setWritable(true, true);
            file.setReadable(true, true);
        }
    }

    /**
     * Generate a Putty private key file (ppk).
     * 
     * @param pair
     *            the key pair
     * @param comment
     *            the comments
     * @param writer
     *            the output the encoding should be
     * @throws IOException
     * @throws NoSuchAlgorithmException
     * @throws InvalidKeyException
     * @see https ://github.com/hierynomus/sshj/blob/master/src/main/java/net/schmizz
     *      /sshj/userauth/keyprovider/PuTTYKeyFile.java
     * @see https://github.com/Yasushi/putty/blob/master/sshpubk.c
     */
    public static void toPrivatePuttyKey(KeyPair pair, String comment, Writer writer) throws IOException, NoSuchAlgorithmException, InvalidKeyException {
        Validate.notNull(pair);
        Validate.notNull(comment);
        Validate.notNull(writer);
        // Remove invalid char from the comment line.
        comment = comment.replaceAll("[\\r\\n]", "");

        // Encode public and private key for putty.
        byte[] publicKeyEncoded = encodePublicKey((RSAPublicKey) pair.getPublic());
        String publicKeyBase64 = encodeBase64(publicKeyEncoded);
        byte[] privateKeyEncoded = encodePrivateKeyForPutty((RSAPrivateCrtKey) pair.getPrivate());
        String privateKeyBase64 = encodeBase64(privateKeyEncoded);

        /*
         * Generate Mac
         */
        MessageDigest digest = MessageDigest.getInstance(ALGORITHM_SHA_1, BC);
        digest.update("putty-private-key-file-mac-key".getBytes());
        final byte[] mackey = digest.digest();

        final Mac mac = Mac.getInstance(ALGORITHM_HMAC_SHA1, BC);
        mac.init(new SecretKeySpec(mackey, 0, 20, mac.getAlgorithm()));

        ByteArrayOutputStream out = new ByteArrayOutputStream();
        DataOutputStream macDataOs = new DataOutputStream(out);
        // String "ssh-rsa"
        macDataOs.writeInt(TYPE.getBytes().length);
        macDataOs.write(TYPE.getBytes());
        // String <encryption>
        macDataOs.writeInt(ENCRYPTION.getBytes().length);
        macDataOs.write(ENCRYPTION.getBytes());
        // String <comment>
        macDataOs.writeInt(comment.getBytes().length);
        macDataOs.write(comment.getBytes());
        // String <public-blob>
        macDataOs.writeInt(publicKeyEncoded.length);
        macDataOs.write(publicKeyEncoded);
        // String <private-blob>
        macDataOs.writeInt(privateKeyEncoded.length);
        macDataOs.write(privateKeyEncoded);
        byte[] macData = out.toByteArray();

        /*
         * Generate ppk file.
         */
        StringBuilder buf = new StringBuilder();
        buf.append("PuTTY-User-Key-File-2: " + TYPE + CRLF);
        buf.append("Encryption: " + ENCRYPTION + CRLF);
        buf.append("Comment: " + comment + CRLF);
        buf.append("Public-Lines: " + countLines(publicKeyBase64, 64) + CRLF);
        for (int i = 0; i < publicKeyBase64.length(); i += 64) {
            buf.append(publicKeyBase64.substring(i, Math.min(publicKeyBase64.length(), i + 64)));
            buf.append(CRLF);
        }
        buf.append("Private-Lines: " + countLines(privateKeyBase64, 64) + CRLF);
        for (int i = 0; i < privateKeyBase64.length(); i += 64) {
            buf.append(privateKeyBase64.substring(i, Math.min(privateKeyBase64.length(), i + 64)));
            buf.append(CRLF);
        }
        buf.append("Private-MAC: " + encodeHex(mac.doFinal(macData)) + CRLF);

        writer.write(buf.toString());
    }

    /**
     * Generate an id_rsa file data.
     * <p>
     * This implementation will use the utf-8 encoding.
     * 
     * @param publicKey
     *            the public key
     * @param comment
     *            the comment
     * @param file
     *            location where to create the file.
     * @throws IOException
     */
    public static void toPublicIdRsa(RSAPublicKey publicKey, String comment, File file) throws IOException {
        FileWriterWithEncoding idrsa = openFileWriter(file, UTF_8);
        toPublicIdRsa(publicKey, comment, idrsa);
        idrsa.close();
        // Set permissions (otherwise SSH complains about file permissions)
        if (SystemUtils.IS_OS_LINUX) {
            file.setExecutable(false, false);
            file.setReadable(false, false);
            file.setWritable(false, false);
            file.setWritable(true, true);
            file.setReadable(true, true);
        }
    }

    /**
     * Generate an id_rsa file data.
     * 
     * @param publicKey
     *            the public key
     * @param comment
     *            the comment
     * @param writer
     *            the destination where to write the data
     * @throws IOException
     */
    public static void toPublicIdRsa(RSAPublicKey publicKey, String comment, Writer writer) throws IOException {
        byte[] encoded = encodePublicKey(publicKey);
        String base64 = encodeBase64(encoded);
        writer.write("ssh-rsa " + base64 + " " + comment);
    }
}
