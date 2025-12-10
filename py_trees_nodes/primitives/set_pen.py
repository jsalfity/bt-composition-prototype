"""
SetPen action node - Controls the turtle's drawing pen.

This node calls the /turtle1/set_pen service to configure pen properties.
"""

import py_trees
from roslibpy import Service, ServiceRequest
from typing import Optional
from ..base_action import BaseActionNode


class SetPen(BaseActionNode):
    """
    Control the turtle's pen settings (color, width, on/off).

    This node calls the /turtle1/set_pen ROS service to configure the pen.

    Args:
        r: Red color value (0-255)
        g: Green color value (0-255)
        b: Blue color value (0-255)
        width: Pen width (default: 3)
        off: Whether pen is off (0) or on (1). Use 1 to disable drawing.
    """

    def __init__(
        self,
        name: str,
        r: int = 255,
        g: int = 255,
        b: int = 255,
        width: int = 3,
        off: int = 0,
        host: str = "localhost",
        port: int = 9090,
    ):
        super().__init__(name, host, port)
        self.r = max(0, min(255, r))  # Clamp to 0-255
        self.g = max(0, min(255, g))
        self.b = max(0, min(255, b))
        self.width = max(1, width)
        self.off = off

        self.set_pen_service: Optional[Service] = None
        self.service_called = False
        self.service_success = False

    def setup(self, **kwargs):
        """Set up ROS service client for /turtle1/set_pen."""
        if not super().setup(**kwargs):
            return False

        try:
            self.set_pen_service = Service(
                self.ros, "/turtle1/set_pen", "turtlesim/SetPen"
            )

            self.logger.info(
                f"SetPen setup complete (r={self.r}, g={self.g}, b={self.b}, width={self.width}, off={self.off})"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to set up SetPen service: {e}")
            return False

    def initialise(self):
        """Initialize when first ticked."""
        super().initialise()
        self.logger.info(
            f"Setting pen: RGB({self.r},{self.g},{self.b}), width={self.width}, off={self.off}"
        )

    def update(self) -> py_trees.common.Status:
        """
        Update the behavior - call the set_pen service synchronously.

        Returns:
            SUCCESS: Service call completed successfully
            FAILURE: ROS not connected or service call failed
        """
        if not self.ros_connected:
            return py_trees.common.Status.FAILURE

        # Make synchronous service call with timeout
        try:
            import time

            request = ServiceRequest(
                {
                    "r": self.r,
                    "g": self.g,
                    "b": self.b,
                    "width": self.width,
                    "off": self.off,
                }
            )

            # Set up result tracking
            result_received = {"success": False, "done": False}

            def success_callback(result):
                result_received["success"] = True
                result_received["done"] = True

            def error_callback(error):
                result_received["success"] = False
                result_received["done"] = True
                self.logger.error(f"SetPen service error: {error}")

            # Call service
            self.set_pen_service.call(request, success_callback, error_callback)

            # Wait for response (with timeout)
            timeout = 2.0  # 2 second timeout
            start_time = time.time()
            while not result_received["done"] and (time.time() - start_time) < timeout:
                time.sleep(0.01)

            if result_received["done"] and result_received["success"]:
                self.logger.info("Pen settings updated successfully")
                return py_trees.common.Status.SUCCESS
            elif result_received["done"]:
                self.logger.error("SetPen service call failed")
                return py_trees.common.Status.FAILURE
            else:
                self.logger.error("SetPen service call timed out")
                return py_trees.common.Status.FAILURE

        except Exception as e:
            self.logger.error(f"Failed to call set_pen service: {e}")
            return py_trees.common.Status.FAILURE

    def terminate(self, new_status: py_trees.common.Status):
        """Clean up on termination."""
        super().terminate(new_status)


# Convenience classes for common pen operations


class PenUp(SetPen):
    """Convenience class to lift the pen (disable drawing)."""

    def __init__(self, name: str = "PenUp", host: str = "localhost", port: int = 9090):
        super().__init__(
            name, r=255, g=255, b=255, width=3, off=1, host=host, port=port
        )


class PenDown(SetPen):
    """Convenience class to lower the pen (enable drawing) with default color."""

    def __init__(
        self,
        name: str = "PenDown",
        r: int = 255,
        g: int = 255,
        b: int = 255,
        width: int = 3,
        host: str = "localhost",
        port: int = 9090,
    ):
        super().__init__(name, r=r, g=g, b=b, width=width, off=0, host=host, port=port)
