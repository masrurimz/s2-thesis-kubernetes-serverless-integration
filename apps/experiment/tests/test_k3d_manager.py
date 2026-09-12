from unittest.mock import MagicMock, patch


class TestApplyNodeResources:
    """Verify apply_node_resources() issues correct docker update commands."""

    @patch("infra.cluster.k3d.manager.run")
    def test_issues_docker_update_for_all_three_nodes(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        from infra.cluster.k3d.manager import K3dManager

        mgr = K3dManager()
        mgr.apply_node_resources()

        docker_calls = [
            c.args[0]
            for c in mock_run.call_args_list
            if len(c.args) > 0 and c.args[0][0] == "docker" and c.args[0][1] == "update"
        ]
        assert len(docker_calls) == 3

    @patch("infra.cluster.k3d.manager.run")
    def test_agent0_gets_1_cpu(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        from infra.cluster.k3d.manager import K3dManager

        mgr = K3dManager()
        mgr.apply_node_resources()

        agent0_calls = [
            c.args[0]
            for c in mock_run.call_args_list
            if len(c.args) > 0 and any("agent-0" in str(a) for a in c.args[0])
        ]
        assert len(agent0_calls) > 0
        call = agent0_calls[0]
        cpus_idx = call.index("--cpus")
        assert call[cpus_idx + 1] == "1.0"

    @patch("infra.cluster.k3d.manager.run")
    def test_workload_node_gets_1_cpu(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        from infra.cluster.k3d.manager import K3dManager

        mgr = K3dManager()
        mgr.apply_node_resources()

        agent1_calls = [
            c.args[0]
            for c in mock_run.call_args_list
            if len(c.args) > 0 and any("agent-1" in str(a) for a in c.args[0])
        ]
        assert len(agent1_calls) > 0
        call = agent1_calls[0]
        cpus_idx = call.index("--cpus")
        assert call[cpus_idx + 1] == "1.0"

    @patch("infra.cluster.k3d.manager.run")
    def test_server_node_gets_1_cpu(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        from infra.cluster.k3d.manager import K3dManager

        mgr = K3dManager()
        mgr.apply_node_resources()

        server_calls = [
            c.args[0]
            for c in mock_run.call_args_list
            if len(c.args) > 0 and any("server-0" in str(a) for a in c.args[0])
        ]
        assert len(server_calls) > 0
        call = server_calls[0]
        cpus_idx = call.index("--cpus")
        assert call[cpus_idx + 1] == "1.0"

    @patch("infra.cluster.k3d.manager.run")
    def test_tolerates_docker_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr="error")
        from infra.cluster.k3d.manager import K3dManager

        mgr = K3dManager()
        # Should not raise
        mgr.apply_node_resources()


class TestLabelNodes:
    """Verify _label_nodes() issues correct kubectl label commands."""

    @patch("infra.cluster.k3d.manager.run")
    def test_issues_kubectl_label_for_all_nodes(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        from infra.cluster.k3d.manager import K3dManager

        mgr = K3dManager()
        mgr._label_nodes()

        label_calls = [
            c.args[0]
            for c in mock_run.call_args_list
            if len(c.args) > 0 and c.args[0][:3] == ["kubectl", "label", "node"]
        ]
        assert len(label_calls) == 3

    @patch("infra.cluster.k3d.manager.run")
    def test_server_labeled_system(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        from infra.cluster.k3d.manager import K3dManager

        mgr = K3dManager()
        mgr._label_nodes()

        server_calls = [
            " ".join(c.args[0])
            for c in mock_run.call_args_list
            if len(c.args) > 0 and any("server-0" in str(a) for a in c.args[0])
        ]
        assert any("node-type=system" in s for s in server_calls)

    @patch("infra.cluster.k3d.manager.run")
    def test_agent0_labeled_workload(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        from infra.cluster.k3d.manager import K3dManager

        mgr = K3dManager()
        mgr._label_nodes()

        agent0_calls = [
            " ".join(c.args[0])
            for c in mock_run.call_args_list
            if len(c.args) > 0 and any("agent-0" in str(a) for a in c.args[0])
        ]
        assert any("node-type=workload" in s for s in agent0_calls)

    @patch("infra.cluster.k3d.manager.run")
    def test_agent1_labeled_workload(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        from infra.cluster.k3d.manager import K3dManager

        mgr = K3dManager()
        mgr._label_nodes()

        agent1_calls = [
            " ".join(c.args[0])
            for c in mock_run.call_args_list
            if len(c.args) > 0 and any("agent-1" in str(a) for a in c.args[0])
        ]
        assert any("node-type=workload" in s for s in agent1_calls)


class TestKnativeInstallerNodeIsolation:
    """Verify KnativeInstaller._configure_node_isolation() applies both patches."""

    @patch("infra.serverless.knative.installer.run")
    def test_configures_podspec_nodeselector(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        from infra.serverless.knative.installer import KnativeInstaller

        installer = KnativeInstaller()
        installer._configure_node_isolation()

        all_calls = [" ".join(c.args[0]) for c in mock_run.call_args_list if c.args]
        assert any("config-features" in s and "podspec-nodeselector" in s for s in all_calls)

    @patch("infra.serverless.knative.installer.run")
    def test_patches_kourier_gateway_to_infra(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        from infra.serverless.knative.installer import KnativeInstaller

        installer = KnativeInstaller()
        installer._configure_node_isolation()

        all_calls = [" ".join(c.args[0]) for c in mock_run.call_args_list if c.args]
        assert any("kourier-gateway" in s and "node-type" in s for s in all_calls)

    @patch("infra.serverless.knative.installer.run")
    def test_kourier_patch_tolerates_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr="not found")
        from infra.serverless.knative.installer import KnativeInstaller

        installer = KnativeInstaller()
        # Should not raise even if kourier patch fails (check=False)
        installer._configure_node_isolation()
