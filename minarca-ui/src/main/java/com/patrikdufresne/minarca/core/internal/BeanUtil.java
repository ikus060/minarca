/*
 * Copyright (c) 2013, Bell Canada All rights reserved.
 * Bell Canada PROPRIETARY/CONFIDENTIAL. Use is subject to license terms.
 */
/*
 * Copyright (c) 2014, Patrik Dufresne Service Logiciel. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.core.internal;

import java.beans.BeanInfo;
import java.beans.IntrospectionException;
import java.beans.Introspector;
import java.beans.PropertyDescriptor;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.List;

/**
 * Utility class to read / write property. This implementation is specifically design to lowercase the first letter of
 * the property name.
 * 
 * @author Patrik Dufresne
 * 
 */
public class BeanUtil {

    /**
     * Goes recursively into the interface and gets all defined propertyDescriptors
     * 
     * @param propertyDescriptors
     *            The result list of all PropertyDescriptors the given interface defines (hierarchical)
     * @param iface
     *            The interface to fetch the PropertyDescriptors
     * @throws IntrospectionException
     */
    static void getInterfacePropertyDescriptors(List propertyDescriptors, Class iface) throws IntrospectionException {
        BeanInfo beanInfo = Introspector.getBeanInfo(iface);
        PropertyDescriptor[] pds = beanInfo.getPropertyDescriptors();
        for (int i = 0; i < pds.length; i++) {
            PropertyDescriptor pd = pds[i];
            propertyDescriptors.add(pd);
        }
        Class[] subIntfs = iface.getInterfaces();
        for (int j = 0; j < subIntfs.length; j++) {
            getInterfacePropertyDescriptors(propertyDescriptors, subIntfs[j]);
        }
    }

    /**
     * @param beanClass
     * @param propertyName
     * @return the PropertyDescriptor for the named property on the given bean class
     */
    public static PropertyDescriptor getPropertyDescriptor(Class beanClass, String propertyName) {
        if (!beanClass.isInterface()) {
            BeanInfo beanInfo;
            try {
                beanInfo = Introspector.getBeanInfo(beanClass);
            } catch (IntrospectionException e) {
                // cannot introspect, give up
                return null;
            }
            PropertyDescriptor[] propertyDescriptors = beanInfo.getPropertyDescriptors();
            for (int i = 0; i < propertyDescriptors.length; i++) {
                PropertyDescriptor descriptor = propertyDescriptors[i];
                if (descriptor.getName().equals(propertyName)) {
                    return descriptor;
                }
            }
        } else {
            try {
                PropertyDescriptor propertyDescriptors[];
                List pds = new ArrayList();
                getInterfacePropertyDescriptors(pds, beanClass);
                if (pds.size() > 0) {
                    propertyDescriptors = (PropertyDescriptor[]) pds.toArray(new PropertyDescriptor[pds.size()]);
                    PropertyDescriptor descriptor;
                    for (int i = 0; i < propertyDescriptors.length; i++) {
                        descriptor = propertyDescriptors[i];
                        if (descriptor.getName().equals(propertyName)) return descriptor;
                    }
                }
            } catch (IntrospectionException e) {
                // cannot introspect, give up
                return null;
            }
        }
        return null;
    }

    public static PropertyDescriptor[] getPropertyDescriptors(Class beanClass) {
        if (!beanClass.isInterface()) {
            BeanInfo beanInfo;
            try {
                beanInfo = Introspector.getBeanInfo(beanClass);
            } catch (IntrospectionException e) {
                // cannot introspect, give up
                return null;
            }
            return beanInfo.getPropertyDescriptors();
        }
        try {
            PropertyDescriptor propertyDescriptors[];
            List pds = new ArrayList();
            getInterfacePropertyDescriptors(pds, beanClass);
            if (pds.size() > 0) {
                return (PropertyDescriptor[]) pds.toArray(new PropertyDescriptor[pds.size()]);
            }
        } catch (IntrospectionException e) {
            // cannot introspect, give up
            return null;
        }
        return null;
    }

    /**
     * Read a bean property.
     * 
     * @param source
     *            the bean
     * @param propertyDescriptor
     *            the property to be read
     * @return the property value.
     */
    public static Object readProperty(Object source, PropertyDescriptor propertyDescriptor) throws IllegalArgumentException {
        try {
            Method readMethod = propertyDescriptor.getReadMethod();
            if (readMethod == null) {
                throw new IllegalArgumentException(propertyDescriptor.getName() + " property does not have a read method."); //$NON-NLS-1$
            }
            if (!readMethod.isAccessible()) {
                readMethod.setAccessible(true);
            }
            return readMethod.invoke(source, (Object[]) null);
        } catch (InvocationTargetException e) {
            throw new IllegalArgumentException(e.getCause());
        } catch (IllegalAccessException e) {
            throw new IllegalArgumentException(e);
        }
    }

    /**
     * Read a bean property.
     * 
     * @param source
     *            the bean
     * @param propertyName
     *            the property to be read
     * @return the property value.
     */
    public static Object readProperty(Object source, String propertyName) {
        PropertyDescriptor property = getPropertyDescriptor(source.getClass(), propertyName);
        if (property == null) {
            throw new IllegalArgumentException(propertyName + " property not found");
        }
        return readProperty(source, property);
    }

    /**
     * Write a bean property.
     * 
     * @param source
     *            the bean
     * @param propertyDescriptor
     *            the property to write
     * @param value
     *            the new property value.
     * @throws IllegalAccessException
     * @throws IllegalArgumentException
     */
    public static void writeProperty(Object source, PropertyDescriptor propertyDescriptor, Object value) throws IllegalArgumentException {
        try {
            Method writeMethod = propertyDescriptor.getWriteMethod();
            if (null == writeMethod) {
                throw new IllegalArgumentException("Missing public setter method for " //$NON-NLS-1$
                        + propertyDescriptor.getName()
                        + " property"); //$NON-NLS-1$
            }
            if (!writeMethod.isAccessible()) {
                writeMethod.setAccessible(true);
            }
            writeMethod.invoke(source, new Object[] { value });
        } catch (InvocationTargetException e) {
            throw new IllegalArgumentException(e.getCause());
        } catch (IllegalAccessException e) {
            throw new IllegalArgumentException(e);
        }
    }

    /**
     * Write a bean property.
     * 
     * @param source
     *            the bean
     * @param propertyName
     *            the property name
     * @param value
     *            the new property value
     * @throws IllegalAccessException
     * @throws IllegalArgumentException
     */
    public static void writeProperty(Object source, String propertyName, Object value) throws IllegalArgumentException {
        PropertyDescriptor property = getPropertyDescriptor(source.getClass(), propertyName);
        if (property == null) {
            throw new IllegalArgumentException(propertyName + " property not found");
        }
        writeProperty(source, property, value);
    }

    /**
     * Private constructor for utility class.
     */
    private BeanUtil() {
        // Nothing to do.
    }

}
