import * as pulumi from "@pulumi/pulumi";
import * as gcp from "@pulumi/gcp";
import * as k8s from "@pulumi/kubernetes";

// Get configuration
const config = new pulumi.Config();
const projectId = config.get("gcp:project") || "styleme-475201";
const region = config.get("gcp:region") || "us-central1";
const zone = config.get("gcp:zone") || "us-central1-a";
const clusterName = config.get("clusterName") || "styleme-cluster";
const nodeCount = config.getNumber("nodeCount") || 2;
const gpuNodeCount = config.getNumber("gpuNodeCount") || 1;

// Enable required GCP APIs
const containerApi = new gcp.projects.Service("container-api", {
    project: projectId,
    service: "container.googleapis.com",
    disableOnDestroy: false,
});

const computeApi = new gcp.projects.Service("compute-api", {
    project: projectId,
    service: "compute.googleapis.com",
    disableOnDestroy: false,
});

// Create GKE cluster
const cluster = new gcp.container.Cluster("styleme-cluster", {
    name: clusterName,
    location: "us-central1-b",  // Use zone b for GPU availability
    project: projectId,
    
    // Remove default node pool (we'll create custom ones)
    removeDefaultNodePool: true,
    initialNodeCount: 1,
    
    // Network configuration
    network: "default",
    subnetwork: "default",
    
    // Enable required features
    minMasterVersion: "latest",
    
    // Enable workload identity for better GCP integration
    workloadIdentityConfig: {
        workloadPool: `${projectId}.svc.id.goog`,
    },
    
    // Enable private cluster (optional, set to false for public access)
    privateClusterConfig: {
        enablePrivateNodes: false,
        enablePrivateEndpoint: false,
    },
    
    // Enable network policy
    networkPolicy: {
        enabled: true,
    },
    
    // Enable logging and monitoring
    loggingService: "logging.googleapis.com/kubernetes",
    monitoringService: "monitoring.googleapis.com/kubernetes",
    
    // Resource labels
    resourceLabels: {
        project: "styleme",
        environment: "production",
    },
}, {
    dependsOn: [containerApi, computeApi],
});

// NOTE: Node pools already exist in GCP - commenting out to avoid update conflicts
// The node pools will continue to work, we just won't manage them through Pulumi for now
// Uncomment and fix if you need to update node pool configuration

// Create default node pool (for regular workloads)
/* const defaultNodePool = new gcp.container.NodePool("default-node-pool", {
    name: "default-pool",
    location: "us-central1-b",  // Use zone b for GPU availability
    cluster: cluster.name,
    project: projectId,
    
    nodeCount: nodeCount,  // Back to configured node count (zone-specific cluster)
    
    nodeConfig: {
        machineType: "n1-standard-2",
        diskSizeGb: 50,  // Back to 50GB (zone-specific cluster, less total quota needed)
        diskType: "pd-standard",
        
        oauthScopes: [
            "https://www.googleapis.com/auth/compute",
            "https://www.googleapis.com/auth/devstorage.read_only",
            "https://www.googleapis.com/auth/logging.write",
            "https://www.googleapis.com/auth/monitoring",
        ],
        
        labels: {
            workload: "default",
        },
        
        // Enable workload identity
        workloadMetadataConfig: {
            mode: "GKE_METADATA",
        },
    },
    
    management: {
        autoRepair: true,
        autoUpgrade: true,
    },
    
    autoscaling: {
        minNodeCount: 1,
        maxNodeCount: 5,
    },
    
    // Add upgrade settings to make updates valid
    upgradeSettings: {
        maxSurge: 1,
        maxUnavailable: 0,
    },
}, {
    dependsOn: [cluster],
    // Protect node pools from accidental deletion
    protect: true,
}); */

// Create GPU node pool (for training workloads)
/* const gpuNodePool = new gcp.container.NodePool("gpu-node-pool", {
    name: "gpu-pool",
    location: "us-central1-b",  // Use zone b for GPU availability
    cluster: cluster.name,
    project: projectId,
    
    nodeCount: gpuNodeCount,
    
    nodeConfig: {
        machineType: "n1-standard-4",
        diskSizeGb: 50,  // Back to 50GB (zone-specific cluster, less total quota needed)
        diskType: "pd-standard",  // Changed from pd-ssd to pd-standard to reduce quota usage
        
        // GPU configuration
        guestAccelerators: [{
            type: "nvidia-tesla-t4",
            count: 1,
        }],
        
        oauthScopes: [
            "https://www.googleapis.com/auth/compute",
            "https://www.googleapis.com/auth/devstorage.read_only",
            "https://www.googleapis.com/auth/logging.write",
            "https://www.googleapis.com/auth/monitoring",
        ],
        
        labels: {
            workload: "gpu",
            accelerator: "nvidia-tesla-t4",
        },
        
        // Note: GKE automatically adds nvidia.com/gpu taint for GPU nodes
        // Only add if not already present
        taints: [],
        
        workloadMetadataConfig: {
            mode: "GKE_METADATA",
        },
    },
    
    management: {
        autoRepair: true,
        autoUpgrade: true,
    },
    
    autoscaling: {
        minNodeCount: 0,  // Scale to zero when not in use
        maxNodeCount: 2,
    },
    
    // Add upgrade settings to make updates valid
    upgradeSettings: {
        maxSurge: 1,
        maxUnavailable: 0,
    },
}, {
    dependsOn: [cluster],
    // Protect node pools from accidental deletion
    protect: true,
}); */

// Create Kubernetes provider using the system kubeconfig
// This uses the kubeconfig from gcloud container clusters get-credentials
// which properly handles GKE authentication
const k8sProvider = new k8s.Provider("k8s-provider", {
    // Use system kubeconfig - assumes gcloud get-credentials has been run
    // This avoids TLS certificate issues with hardcoded IP addresses
    kubeconfig: process.env.KUBECONFIG || undefined, // Use KUBECONFIG env var if set, otherwise use default
}, {
    dependsOn: [cluster], // defaultNodePool commented out
});

// Deploy Kubernetes manifests
// We'll deploy the manifests we created earlier

// 1. ConfigMap
const configMap = new k8s.core.v1.ConfigMap("styleme-config", {
    metadata: {
        name: "styleme-config",
        namespace: "default",
        labels: {
            app: "styleme",
        },
    },
    data: {
        "GCP_BUCKET_NAME": "styleme-data-bucket",
        "GCP_PROJECT_ID": projectId,
        "DATA_PREFIX": "json",
        "IMAGES_PREFIX": "images",
        "LOG_LEVEL": "INFO",
        "DATA_DIR": "/app/data",
        // Use GCS paths for experiments since models come from Vertex AI training
        "EXPERIMENTS_DIR": "/gcs/styleme-production/experiments",
        "CATALOG_DIR": "/gcs/styleme-production/catalog",
        "WARDROBES_DIR": "/gcs/styleme-production/wardrobes",
        "QUERIES_DIR": "/gcs/styleme-production/queries",
        "RESULTS_DIR": "/gcs/styleme-production/results",
        "LOGS_DIR": "/app/logs",
        "PORT": "5000",
        "FLASK_DEBUG": "false",
        "UPLOAD_FOLDER": "/app/uploads",
        "RUN_API_SERVER": "true",
        "CUDA_VISIBLE_DEVICES": "0",
    },
}, { provider: k8sProvider });

// 2. PersistentVolumeClaim
const pvc = new k8s.core.v1.PersistentVolumeClaim("styleme-data-pvc", {
    metadata: {
        name: "styleme-data-pvc",
        namespace: "default",
        labels: {
            app: "styleme",
        },
    },
    spec: {
        accessModes: ["ReadWriteOnce"],  // Changed to ReadWriteOnce to match k8s YAML and GKE compatibility
        resources: {
            requests: {
                storage: "50Gi",
            },
        },
    },
}, { provider: k8sProvider, dependsOn: [k8sProvider] });

// Deploy all Kubernetes manifests from the k8s directory
// We'll deploy them in order to respect dependencies

// IMPORTANT: Kubernetes Jobs are IMMUTABLE - they cannot be updated once created.
// If you get an error about immutable fields when updating, you MUST delete the jobs first:
//   kubectl delete job styleme-ingestion styleme-preprocessing
// Then run: pulumi up
// 
// Alternative: Use pulumi destroy on the job resources, then recreate them

// Note: ConfigMap and PVC are already created above, so we deploy the rest
const ingestionJob = new k8s.yaml.ConfigFile("ingestion-job", {
    file: "../../k8s/03-ingestion-job.yaml",
}, { provider: k8sProvider, dependsOn: [k8sProvider, pvc, configMap] });

const preprocessingJob = new k8s.yaml.ConfigFile("preprocessing-job", {
    file: "../../k8s/04-preprocessing-job.yaml",
}, { provider: k8sProvider, dependsOn: [k8sProvider, ingestionJob] });

// NOTE: Training is now done via Vertex AI, not Kubernetes
// Use scripts/submit_vertex_ai_training.sh to submit training jobs
// The k8s training job is kept for reference but not deployed
// const trainingJob = new k8s.yaml.ConfigFile("training-job", {
//     file: "../../k8s/05-training-job.yaml",
// }, { provider: k8sProvider, dependsOn: [k8sProvider, preprocessingJob] }); // gpuNodePool commented out

// Inference deployment - no longer depends on k8s training job
// Training models are stored in GCS (from Vertex AI) and loaded by inference service
const inferenceDeployment = new k8s.yaml.ConfigFile("inference-deployment", {
    file: "../../k8s/06-inference-deployment.yaml",
}, { provider: k8sProvider, dependsOn: [k8sProvider, preprocessingJob] });

// Horizontal Pod Autoscaler for inference service
const inferenceHPA = new k8s.yaml.ConfigFile("inference-hpa", {
    file: "../../k8s/07-horizontal-pod-autoscaler.yaml",
}, { provider: k8sProvider, dependsOn: [k8sProvider, inferenceDeployment] });

// NOTE: Retraining CronJob is commented out because:
// 1. Training is now done via Vertex AI (not Kubernetes)
// 2. The CronJob would need to be updated to trigger Vertex AI training instead
// 3. For now, use manual Vertex AI training or update the CronJob separately
// If you want automated retraining, update 08-retraining-cronjob.yaml to call Vertex AI API
// const retrainingCronJob = new k8s.yaml.ConfigFile("retraining-cronjob", {
//     file: "../../k8s/08-retraining-cronjob.yaml",
// }, { provider: k8sProvider, dependsOn: [k8sProvider, inferenceDeployment] });

// Export important outputs
export const exportedClusterName = cluster.name;
export const exportedClusterEndpoint = cluster.endpoint;
export const exportedClusterLocation = cluster.location;
export const kubeconfig = pulumi.secret(
    pulumi.all([cluster.name, cluster.endpoint]).apply(([name, endpoint]) => {
        const context = `${projectId}_us-central1-b_${name}`;  // Use zone b to match cluster location
        return `apiVersion: v1
clusters:
- cluster:
    server: https://${endpoint}
  name: ${context}
contexts:
- context:
    cluster: ${context}
    user: ${context}
  name: ${context}
current-context: ${context}
kind: Config
preferences: {}
users:
- name: ${context}
  user:
    exec:
      apiVersion: client.authentication.k8s.io/v1beta1
      command: gke-gcloud-auth-plugin
      installHint: Install gke-gcloud-auth-plugin for use with kubectl by following
        https://cloud.google.com/blog/products/containers-kubernetes/kubectl-auth-changes-in-gke
      provideClusterInfo: true
`;
    })
);

