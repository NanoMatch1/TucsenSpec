from tucsenspec.TUCam import *

class TUextra:

    def __init__(self, camera):
        self.camera = camera
        self.camera_parameters = {}
        self.camera_capabilities = {}

    

    def camera_info(self):
        """Prints the camera info obtained by get_camera_parameters."""
        if len(self.camera_parameters) == 0 or len(self.camera_capabilities) == 0:
            self.get_camera_parameters()

        print("Camera Parameters:")
        for key, parameters in self.camera_parameters.items():
            # print(f"  {key}: {value}")
            print(f"{key}:")
            for param_key, param_value in parameters.items():
                print(f"  {param_key}: {param_value}")

        print("\nCamera Capabilities:")
        for key, capabilities in self.camera_capabilities.items():
            # print(f"  {key}: {value}")
            print(f"{key}:")
            for cap_key, cap_value in capabilities.items():
                print(f"  {cap_key}: {cap_value}")
        

    def get_camera_parameters(self):
        """
        Retrieves and prints all available properties and capabilities of the camera.
        Handles unknown return values gracefully.
        """
        if not hasattr(self, "TUCAMOPEN") or self.TUCAMOPEN.hIdxTUCam == 0:
            print("Error: Camera not initialized or opened.")
            return

        print("\n=== Camera Properties ===")
        for prop in TUCAM_IDPROP:
            try:
                prop_attr = TUCAM_PROP_ATTR()
                prop_attr.idProp = prop.value
                status = TUCAM_Prop_GetAttr(self.TUCAMOPEN.hIdxTUCam, byref(prop_attr))

                if status == TUCAMRET.TUCAMRET_SUCCESS:
                    print(f"{prop.name}:")
                    print(f"  Min: {prop_attr.dbValMin}")
                    print(f"  Max: {prop_attr.dbValMax}")
                    print(f"  Default: {prop_attr.dbValDft}")
                    print(f"  Step: {prop_attr.dbValStep}")

                    # Save the parameters for later use
                    self.camera_parameters[prop.name] = {
                        "min": prop_attr.dbValMin,
                        "max": prop_attr.dbValMax,
                        "default": prop_attr.dbValDft,
                        "step": prop_attr.dbValStep
                    }

                else:
                    print(f"{prop.name}: Not Available (Error Code: {status})")

            except Exception as e:
                print(f"{prop.name}: Error - {str(e)}")

        print("\n=== Camera Capabilities ===")
        for capa in TUCAM_IDCAPA:
            try:
                capa_attr = TUCAM_CAPA_ATTR()
                capa_attr.idCapa = capa.value
                status = TUCAM_Capa_GetAttr(self.TUCAMOPEN.hIdxTUCam, byref(capa_attr))

                if status == TUCAMRET.TUCAMRET_SUCCESS:
                    print(f"{capa.name}:")
                    print(f"  Min: {capa_attr.nValMin}")
                    print(f"  Max: {capa_attr.nValMax}")
                    print(f"  Default: {capa_attr.nValDft}")
                    print(f"  Step: {capa_attr.nValStep}")

                    # Save the capabilities for later use
                    self.camera_capabilities[capa.name] = {
                        "min": capa_attr.nValMin,
                        "max": capa_attr.nValMax,
                        "default": capa_attr.nValDft,
                        "step": capa_attr.nValStep
                    }

                else:
                    print(f"{capa.name}: Not Available (Error Code: {status})")

            except Exception as e:
                print(f"{capa.name}: Error - {str(e)}")

        print(f"Camera Parameters: {len(self.camera_parameters)}")
        print(f"Camera Capabilities: {len(self.camera_capabilities)}")

    def get_gain_attributes(self):
        """
        Get the attributes for the camera gain, including min, max, default, and step values.

        :return: A dictionary with 'min', 'max', 'default', and 'step' values, or None if retrieval fails.
        """
        if not hasattr(self, "TUCAMOPEN") or self.TUCAMOPEN.hIdxTUCam == 0:
            print("Error: Camera not initialized or opened.")
            return None

        attr = TUCAM_PROP_ATTR()
        attr.idProp = TUCAM_IDPROP.TUIDP_GLOBALGAIN.value
        status = TUCAM_Prop_GetAttr(self.TUCAMOPEN.hIdxTUCam, byref(attr))

        if status == TUCAMRET.TUCAMRET_SUCCESS:
            return {
                "min": attr.dbValMin,
                "max": attr.dbValMax,
                "default": attr.dbValDft,
                "step": attr.dbValStep
            }
        else:
            print(f"Failed to get camera gain attributes. Error code: {status}")
            return None
    