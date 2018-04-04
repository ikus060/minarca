/*
 * Copyright (C) 2018, Patrik Dufresne Service Logiciel inc. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.ui;

import org.eclipse.jface.resource.FontRegistry;
import org.eclipse.jface.resource.JFaceResources;
import org.eclipse.swt.SWT;
import org.eclipse.swt.custom.CTabFolder;
import org.eclipse.swt.graphics.Color;
import org.eclipse.swt.graphics.Font;
import org.eclipse.swt.graphics.FontData;
import org.eclipse.swt.graphics.RGB;
import org.eclipse.swt.program.Program;
import org.eclipse.swt.widgets.Button;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.swt.widgets.Control;
import org.eclipse.swt.widgets.Display;
import org.eclipse.swt.widgets.Label;
import org.eclipse.ui.forms.FormColors;
import org.eclipse.ui.forms.events.HyperlinkAdapter;
import org.eclipse.ui.forms.events.HyperlinkEvent;
import org.eclipse.ui.forms.events.IHyperlinkListener;
import org.eclipse.ui.forms.widgets.FormText;
import org.eclipse.ui.forms.widgets.FormToolkit;

/**
 * Customized implementation of FormToolkit to provide more font and color related to this application.
 * 
 * @author Patrik Dufresne
 * 
 */
public class AppFormToolkit extends FormToolkit {

    private static final String ALT_BG = "ALT_BG";
    private static final String ALT_FG = "ALT_FG";
    private static final int FORM_TEXT_MARGNIN = 10;
    private static final String H = "H";
    private static final String H_HOVER = "H_HOVER";
    private static final String H1 = "h1";
    private static final String H2 = "h2";
    private static final String H3 = "h3";
    private static final String H4 = "h4";
    private static final String LIGHT = "light";
    private static final String WARN_BG = "WARN_BG";
    private static final String WARN_FG = "WARN_FG";

    protected static Font getFont(String symbolicname, float size, boolean bold) {
        String newSymbolicName = symbolicname + "." + size;
        FontRegistry registry = JFaceResources.getFontRegistry();
        if (!registry.hasValueFor(newSymbolicName)) {
            FontData[] data = registry.getFontData(symbolicname).clone();
            for (int i = 0; i < data.length; i++) {
                data[i] = new FontData(data[i].getName(), data[i].getHeight(), data[i].getStyle());
                data[i].setHeight(Math.round(size * data[i].getHeight()));
            }
            registry.put(newSymbolicName, data);
        }
        return bold ? registry.getBold(newSymbolicName) : registry.get(newSymbolicName);
    }

    public static Font getFontBold(String symbolicname) {
        FontRegistry registry = JFaceResources.getFontRegistry();
        return registry.getBold(symbolicname);
    }

    public static Font getFontItalic(String symbolicname) {
        FontRegistry registry = JFaceResources.getFontRegistry();
        return registry.getItalic(symbolicname);
    }

    public static RGB rgb(String color) {
        return new RGB(Integer.valueOf(color.substring(1, 3), 16), Integer.valueOf(color.substring(3, 5), 16), Integer.valueOf(color.substring(5, 7), 16));
    }

    private IHyperlinkListener hyperlinkListener;

    /**
     * Create a form tool kit using default color.
     * 
     * @param display
     */
    public AppFormToolkit(Display display) {
        this(display, false);
    }

    /**
     * Create a form tool kit for minarca.
     * 
     * @param display
     * @param useAltColor
     *            True to use alternative colors.
     */
    public AppFormToolkit(Display display, boolean useAltColor) {
        super(display);
        refreshHyperlinkColors();
    }

    /**
     * This implementation adjust the colors according to the control type.
     */
    @Override
    public void adapt(Composite composite) {
        adapt(composite, false);
    }

    /**
     * This implementation adjust the colors according to the control type.
     */
    public void adapt(Composite composite, boolean useAltColor) {
        super.adapt(composite);
        if (useAltColor) {
            composite.setBackground(getAltBackground());
        }
    }

    /**
     * This implementation adjust the colors according to the control type.
     */
    public void adapt(Control control, boolean trackFocus, boolean trackKeyboard) {
        adapt(control, trackFocus, trackKeyboard, false);
    }

    /**
     * This implementation adjust the colors according to the control type.
     */
    public void adapt(Control control, boolean trackFocus, boolean trackKeyboard, boolean useAltColor) {
        super.adapt(control, trackFocus, trackKeyboard);
        if (useAltColor) {
            if (control instanceof Label || control instanceof FormText) {
                control.setBackground(getAltBackground());
                control.setForeground(getAltForeground());
            }
            if (control instanceof Button) {
                control.setBackground(getAltBackground());
            }
        }
    }

    public Label createAppnameLabel(Composite parent, String text, int style) {
        Label label = createLabel(parent, text, style);
        label.setFont(getFont(JFaceResources.DEFAULT_FONT, 3.25f, false));
        return label;
    }

    /**
     * Create composite.
     * 
     * @param parent
     * @param style
     * @param useAltColor
     * @return
     */
    public Composite createComposite(Composite parent, int style, boolean useAltColor) {
        Composite comp = createComposite(parent, style);
        adapt(comp, useAltColor);
        return comp;
    }

    public CTabFolder createCTabFolder(Composite parent) {
        CTabFolder t = new CTabFolder(parent, SWT.TOP | SWT.FLAT);
        Font f = getFontBold(JFaceResources.DIALOG_FONT);
        t.setSimple(true);
        t.setFont(f);
        // Compute the height of the tab (3 x font height)
        int height = f.getFontData()[0].getHeight();
        t.setTabHeight(height * 3);
        return t;
    }

    @Override
    public FormText createFormText(Composite parent, boolean trackFocus) {
        return createFormText(parent, "", false, false);
    }

    public FormText createFormText(Composite parent, String text) {
        return createFormText(parent, text, false, false);
    }

    public FormText createFormText(Composite parent, String text, boolean withPadding) {
        return createFormText(parent, text, withPadding, false);
    }

    /**
     * Create a default form text.
     * 
     * @param composite
     * @param text
     *            initial form text
     * @param withPadding
     *            True to sets default padding value (current value: 15)
     * @return a FormText widget.
     */
    public FormText createFormText(Composite parent, String text, boolean withPadding, boolean useAltColor) {
        FormText engine = new FormText(parent, SWT.NO_BACKGROUND | SWT.WRAP | SWT.NO_FOCUS) {

            private String replaceTag(String text, String tag, String replacement, String attributes) {
                return text.replace("<" + tag + ">", "<" + replacement + (attributes != null ? " " + attributes : "") + ">").replace(
                        "</" + tag + ">",
                        "</" + replacement + ">");
            }

            @Override
            public void setText(String text, boolean parseTags, boolean expandURLs) {
                // When parse tags is enabled, add some transformation.
                if (!parseTags) {
                    super.setText(text, parseTags, expandURLs);
                }
                // wrap text into a doc and paragraph.
                text = "<doc><p>" + text + "</p></doc>";
                text = replaceTag(text, "strong", "b", null);
                text = replaceTag(text, "h1", "span", "font='h1' color='h1'");
                text = replaceTag(text, "h2", "span", "font='h2' color='h2'");
                text = replaceTag(text, "h3", "span", "font='h3' color='h3'");
                text = replaceTag(text, "h4", "span", "font='h4' color='h4'");
                try {
                    super.setText(text, parseTags, expandURLs);
                } catch (IllegalArgumentException e) {
                    super.setText(text, false, expandURLs);
                }
            }

        };
        if (withPadding) {
            engine.marginWidth = FORM_TEXT_MARGNIN;
            engine.marginHeight = FORM_TEXT_MARGNIN;
        }
        // Add styles
        Color fg = useAltColor ? getAltForeground() : getColors().getForeground();
        // H1,
        engine.setFont(H1, getFont(JFaceResources.DIALOG_FONT, 3.25f, false));
        engine.setColor(H1, fg);
        // H2
        engine.setFont(H2, getFont(JFaceResources.DIALOG_FONT, 2.6f, false));
        engine.setColor(H2, fg);
        // H3
        engine.setFont(H3, getFont(JFaceResources.DIALOG_FONT, 1.7f, false));
        engine.setColor(H3, fg);
        // H4
        engine.setFont(H4, getFont(JFaceResources.DIALOG_FONT, 1.25f, false));
        engine.setColor(H4, fg);
        // LIGHT
        engine.setColor(LIGHT, getLightColor());

        engine.setHyperlinkSettings(getHyperlinkGroup());
        engine.addHyperlinkListener(getHyperlinkListener());
        adapt(engine, false, false, useAltColor);
        engine.setMenu(parent.getMenu());
        engine.setText(text, true, true);
        return engine;
    }

    public void decorateWarningLabel(FormText engine) {
        engine.setBackground(getColors().createColor(WARN_BG, rgb("#e99002")));
        engine.setForeground(getColors().createColor(WARN_FG, rgb("#ffffff")));
    }

    @Override
    public void dispose() {
        super.dispose();
    }

    private Color getAltBackground() {
        return getColors().createColor(ALT_BG, Display.getDefault().getSystemColor(SWT.COLOR_WIDGET_BACKGROUND).getRGB());
    }

    private Color getAltForeground() {
        return getColors().createColor(ALT_FG, rgb("#ffffff"));
    }

    /**
     * Return the default hyperlink lister to open link into browser.
     * 
     * @return
     */
    public IHyperlinkListener getHyperlinkListener() {
        if (this.hyperlinkListener == null) {
            this.hyperlinkListener = new HyperlinkAdapter() {

                @Override
                public void linkActivated(HyperlinkEvent e) {
                    String href = e.getHref() != null ? e.getHref().toString() : null;
                    if (href != null && (href.startsWith("http://") || href.startsWith("https://"))) {
                        Program.launch(href);
                    }
                }
            };
        }
        return this.hyperlinkListener;
    }

    private Color getLightColor() {
        return getColors().createColor(LIGHT, FormColors.blend(rgb("#ffffff"), getColors().getForeground().getRGB(), 25));
    }

    public void refreshHyperlinkColors(boolean useAltColor) {
        super.refreshHyperlinkColors();
        if (useAltColor) {

        } else {
            getHyperlinkGroup().setForeground(getColors().createColor(H, rgb("#008cba")));
            getHyperlinkGroup().setActiveForeground(getColors().createColor(H_HOVER, FormColors.blend(rgb("#008cba"), rgb("#000000"), 15)));
        }
    }

}
