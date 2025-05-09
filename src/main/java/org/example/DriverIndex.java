/*
package org.example;

import java.io.File;
import java.net.URI;
import java.io.IOException;
import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.FileSystem;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;

public class DriverIndex {
    public static void main(String[] args) throws Exception {
        if (args.length != 3) {
            System.err.println("Usage: DriverIndex <input_dir> <url_mapping_json> <output_dir>");
            System.exit(-1);
        }

        Configuration conf = new Configuration();
        conf.set("mapreduce.framework.name", "local");
        FileSystem fs = FileSystem.getLocal(conf);

        String input = args[0];
        String mappingJson = args[1];
        String output = args[2];





        // Clean up existing output
        if (fs.exists(new Path(output))) {
            fs.delete(new Path(output), true);
        }

        Job job = Job.getInstance(conf, "Inverted Index with URL Mapping");
        job.setJarByClass(DriverIndex.class);

        // before creating the Job:
        URI mappingUri = new File(mappingJson).toURI();
       // e.g. file:///D:/…/url_mapping_final.json
        // Distribute the URL mapping JSON to all mappers
        // The JSON will be symlinked as 'url_mapping.json'
        job.addCacheFile(new URI(mappingUri.toString() + "#url_mapping.json"));

        job.setMapperClass(MapperIndex.class);
        job.setCombinerClass(CombinerIndex.class);
        job.setReducerClass(ReducerIndex.class);

        job.setOutputKeyClass(Text.class);
        job.setOutputValueClass(Text.class);

        FileInputFormat.addInputPath(job, new Path(input));
        FileOutputFormat.setOutputPath(job, new Path(output));

        System.exit(job.waitForCompletion(true) ? 0 : 1);
    }
}*/

package org.example;

import java.io.File;
import java.net.URI;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.LocalFileSystem;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;

public class DriverIndex {
    public static void main(String[] args) throws Exception {
        System.setProperty("hadoop.home.dir", "C:\\hadoop");
        System.load("C:\\hadoop\\bin\\hadoop.dll"); // Load native library
        if (args.length != 3) {
            System.err.println("Usage: DriverIndex <input_dir> <url_mapping_json> <output_dir>");
            System.exit(-1);
        }
        String inputDir      = args[0];
        String mappingJson   = args[1];
        String outputDir     = args[2];

        // ─────────────────────────────────────────────────────────────────
        // 1) Build a config that *only* runs locally (without loading defaults)--->canceld
        Configuration conf = new Configuration(); // load DURABLE defaults
        conf.set("fs.defaultFS", "file:///");
        conf.set("mapreduce.framework.name", "local");
        // Set memory limits (adjust based on your system RAM)
        conf.set("mapreduce.map.memory.mb", "2048");
        conf.set("mapreduce.reduce.memory.mb", "3072");
        conf.set("mapreduce.map.java.opts", "-Xmx1536m");
        conf.set("mapreduce.reduce.java.opts", "-Xmx2560m");

        // Verify configurations
        System.out.println("fs.defaultFS: " + conf.get("fs.defaultFS"));
        System.out.println("mapreduce.framework.name: " + conf.get("mapreduce.framework.name"));

        // 2) Grab the LOCAL filesystem
        LocalFileSystem localFs = LocalFileSystem.getLocal(conf);

        // 3) Clean up any previous output folder
        Path outPath = new Path(outputDir);
        if (localFs.exists(outPath)) {
            localFs.delete(outPath, true);
        }

        // ─────────────────────────────────────────────────────────────────
        // 4) Create the job
        Job job = Job.getInstance(conf, "Inverted Index (Local)");
        job.setJarByClass(DriverIndex.class);

        // Verify job's configuration
        System.out.println("Job's mapreduce.framework.name: " + job.getConfiguration().get("mapreduce.framework.name"));

        // 5) Ship the JSON mapping into each mapper
        URI mapUri = new File(mappingJson).toURI();
        job.addCacheFile(new URI(mapUri.toString() + "#url_mapping.json"));

        job.setMapperClass(MapperIndex.class);
        job.setCombinerClass(CombinerIndex.class);
        job.setReducerClass(ReducerIndex.class);

        job.setOutputKeyClass(Text.class);
        job.setOutputValueClass(Text.class);

        conf.setBoolean("mapreduce.input.FileInputFormat.input.dir.recursive", true);

        FileInputFormat.addInputPath(job, new Path(inputDir));
        FileOutputFormat.setOutputPath(job, outPath);

        // 6) Run and wait
        boolean success = job.waitForCompletion(true);
        System.exit(success ? 0 : 1);
    }
}