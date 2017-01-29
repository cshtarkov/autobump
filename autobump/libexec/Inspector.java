/*
Copyright 2016-2017 Christian Shtarkov

This file is part of Autobump.

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, see <http://www.gnu.org/licenses/>.
*/

import java.net.URL;
import java.net.URLClassLoader;
import java.net.MalformedURLException;

import java.util.Queue;
import java.util.LinkedList;
import java.util.Set;
import java.util.HashSet;

import java.io.File;

import java.lang.reflect.Field;
import java.lang.reflect.Method;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.transform.Transformer;
import javax.xml.transform.TransformerException;
import javax.xml.transform.TransformerFactory;
import javax.xml.transform.dom.DOMSource;
import javax.xml.transform.stream.StreamResult;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

/**
 *
 * Utility program that performs introspection on a list of Java
 * classes and serializes their definitions as XML, which is then printed
 * to stdout.
 *
 * Usage: java Inspector [build-location] [class-names...]
 *   where [build-location] is a path to a directory where the tree of Java classes resides.
 *         [class-names...] is a list of one or more fully-qualified class names.
 *
 * This program is invoked by autobump's Java handler to assist with converting
 * a Java codebase into its internal API representation.
 *
 */
public class Inspector {

    private static DocumentBuilderFactory documentFactory;
    private static DocumentBuilder documentBuilder;
    private static TransformerFactory transformerFactory;
    private static Transformer transformer;

    private static void abort(String message, int status) {
        System.err.println("Inspector: " + message);
        System.exit(status);
    }

    private static void abort(String message) {
        abort(message, 1);
    }

    private static ClassLoader instantiateClassLoader(String bin) throws MalformedURLException {
        URL url = new URL("file://" + bin + File.separator);
        URL[] urls = new URL[] {url};
        ClassLoader loader = new URLClassLoader(urls);
        return loader;
    }

    private static String typeBasename(Class type) {
        if (type.isArray()) {
            return typeBasename(type.getComponentType());
        } else {
            return type.getName();
        }
    }

    private static int typeDimension(Class type) {
        if (type.isArray()) {
            return 1 + typeDimension(type.getComponentType());
        } else {
            return 0;
        }
    }

    private static Element typeToXML(Class type, Document doc) {
        Element e = doc.createElement("type");
        e.setAttribute("name", typeBasename(type));
        e.setAttribute("dimension", String.valueOf(typeDimension(type)));
        return e;
    }

    /**
     * Given an existing document and its root element,
     * append a <class> element representation of a Class.
     */
    private static void classToXML(Class inspected, Set<String> visitedClasses, Document doc, Element root) {
        if (visitedClasses.contains(inspected.getName())) {
            return;
        } else {
            visitedClasses.add(inspected.getName());
        }
        Element newRoot = doc.createElement("class");
        root.appendChild(newRoot);
        root = newRoot;
        root.setAttribute("name", inspected.getName());

        // Fields
        for (Field field : inspected.getFields()) {
            Element fieldNode = doc.createElement("field");
            fieldNode.setAttribute("name", field.getName());
            fieldNode.appendChild(typeToXML(field.getType(), doc));
            root.appendChild(fieldNode);
        }

        // Methods
        for (Method method : inspected.getMethods()) {
            Element methodNode = doc.createElement("method");
            methodNode.setAttribute("name", method.getName());
            methodNode.appendChild(typeToXML(method.getReturnType(), doc));

            // Method signature
            Element signatureNode = doc.createElement("signature");
            Class[] types = method.getParameterTypes();
            for (int i = 0; i < types.length; i++) {
                Element parameterNode = doc.createElement("parameter");
                parameterNode.setAttribute("name", "arg" + String.valueOf(i));
                parameterNode.appendChild(typeToXML(types[i], doc));
                signatureNode.appendChild(parameterNode);
            }
            methodNode.appendChild(signatureNode);
            root.appendChild(methodNode);
        }

        // Inner class or method definitions
        for (Class definition : inspected.getClasses()) {
            classToXML(definition, visitedClasses, doc, root);
        }

    }

    /**
     * Create an XML document with the representation of all classes
     * in the queue.
     */
    private static Document classToXML(Queue<Class> forInspection) {
        Document doc = documentBuilder.newDocument();
        Element root = doc.createElement("introspection");
        doc.appendChild(root);
        while (!forInspection.isEmpty()) {
            classToXML(forInspection.remove(), new HashSet<String>(), doc, root);
        }
        return doc;
    }

    public static void main(String[] args) {

        // Validate and parse arguments
        Queue<Class> forInspection = new LinkedList<Class>();
        if (args.length < 1) {
            abort("Invalid number of arguments: expected [build-location] [class-names...]");
        }

        ClassLoader loader = null;
        try {
            loader = instantiateClassLoader(args[0]);
        } catch(MalformedURLException ex) {
            abort(String.format("%s is not a valid location", args[0]));
        }

        for (int i = 1; i < args.length; i++) {
            try {
                forInspection.add(loader.loadClass(args[i]));
            } catch(ClassNotFoundException ex) {
                abort(String.format("Class %s not found", args[i]));
            } catch(NoClassDefFoundError ex) {
                abort(String.format("Class " + args[i] + " present at compile time, but not now. Is the build root correct?"));
            }
        }

        // Prepare XML machinery
        try {
            documentFactory = DocumentBuilderFactory.newInstance();
            documentBuilder = documentFactory.newDocumentBuilder();
            transformerFactory = TransformerFactory.newInstance();
            transformer = transformerFactory.newTransformer();
        } catch(Exception ex) {
            ex.printStackTrace();
            abort("Something went wrong with XML conversion");
        }

        // Introspect all classes on the queue and print to stdout
        Document classDescription = classToXML(forInspection);
        DOMSource source = new DOMSource(classDescription);
        StreamResult result = new StreamResult(System.out);

        try {
            transformer.transform(source, result);
            System.out.println();
        } catch(TransformerException ex) {
            ex.printStackTrace();
            abort("Something went wrong with XML conversion");
        }
    }
}
