/*
 * Copyright (C) 2018, Patrik Dufresne Service Logiciel inc. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.ui;

import java.util.ArrayList;
import java.util.List;

import org.eclipse.jface.resource.ImageDescriptor;
import org.eclipse.jface.resource.ImageRegistry;
import org.eclipse.jface.resource.JFaceResources;
import org.eclipse.jface.window.Window;
import org.eclipse.swt.graphics.Image;

/**
 * Utility class to manage images.
 * 
 * @author Patrik Dufresne
 * 
 */
public class Images {

    public static final String MINARCA_16_PNG = "minarca_16.png";
    public static final String MINARCA_32_PNG = "minarca_32.png";
    public static final String MINARCA_48_PNG = "minarca_48.png";
    public static final String MINARCA_128_PNG = "minarca_128.png";
    public static final String MINARCA_128_WHITE_PNG = "minarca_128_w.png";

    static {
        ImageRegistry ir = JFaceResources.getImageRegistry();
        ir.put(MINARCA_16_PNG, ImageDescriptor.createFromFile(Main.class, MINARCA_16_PNG));
        ir.put(MINARCA_32_PNG, ImageDescriptor.createFromFile(Main.class, MINARCA_32_PNG));
        ir.put(MINARCA_48_PNG, ImageDescriptor.createFromFile(Main.class, MINARCA_48_PNG));
        ir.put(MINARCA_128_PNG, ImageDescriptor.createFromFile(Main.class, MINARCA_128_PNG));
        ir.put(MINARCA_128_WHITE_PNG, ImageDescriptor.createFromFile(Main.class, MINARCA_128_WHITE_PNG));
    }

    public static void setDefaultImages() {
        // Register image
        ImageRegistry ir = JFaceResources.getImageRegistry();
        List<Image> images = new ArrayList<Image>();
        images.add(ir.get(Images.MINARCA_128_PNG));
        images.add(ir.get(Images.MINARCA_48_PNG));
        images.add(ir.get(Images.MINARCA_32_PNG));
        images.add(ir.get(Images.MINARCA_16_PNG));

        // Sets images.
        Window.setDefaultImages(images.toArray(new Image[images.size()]));
    }

}
